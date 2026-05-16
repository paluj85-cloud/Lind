"""
Game loop — the heart of Lind ADND Engine.

Manages the full player → LLM → world → player cycle:
  1. Greeting ritual (2-step: invitation then personal address)
  2. Player input → first LLM pass (narrative + optional dice request)
  3. Dice result → second LLM pass (outcome narration)
  4. World fact extraction and persistence
  5. Full LLM trace logging
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

from backend.app.config import settings
from backend.app.db import (
    save_message,
    save_world_fact,
    save_llm_trace,
    get_recent_messages,
    get_world_facts,
    get_next_sequence,
)
from backend.app.llm.client import get_llm_client
from backend.app.game.prompts.builder import PromptBuilder
from backend.app.game.prompts.context import ContextFormatter
from backend.app.models import (
    CallType,
    LLMResponse,
    MasterSpeech,
    MasterThinking,
    DiceRollRequest,
)


class GameLoop:
    """
    Manages a single player session's game loop.

    Public API:
      start_greeting(player_name)  → 2 LLM passes, greeting ritual
      handle_player_input(content) → 1st LLM pass (may request dice)
      handle_dice_result(req_id, roll, mod) → 2nd LLM pass (outcome)
    """

    def __init__(
        self,
        session_id: str,
        ws: WebSocket,
        game_log: logging.Logger | None = None,
    ) -> None:
        self.session_id = session_id
        self.ws = ws
        self.log = game_log or logging.getLogger(f"lind.session.{session_id[:8]}")
        self.llm = get_llm_client()
        self.prompts = PromptBuilder()
        self.context_fmt = ContextFormatter()

        # Track the pending dice request (only one at a time)
        self._pending_dice_request_id: str | None = None

    # ── WebSocket helpers ───────────────────────────────────────────────────

    async def _ws_send(self, msg: dict[str, Any]) -> None:
        """Send a JSON message to the WebSocket client."""
        try:
            await self.ws.send_json(msg)
        except Exception as exc:
            self.log.error("WS send failed: %s", exc)

    async def _think_started(self) -> None:
        await self._ws_send(MasterThinking(status="started").model_dump())

    async def _think_stopped(self) -> None:
        await self._ws_send(MasterThinking(status="stopped").model_dump())

    async def _narrate(
        self, text: str, dice_request: dict[str, Any] | None = None
    ) -> None:
        """Send narrator speech to client, optionally with pending dice request."""
        if not text.strip():
            text = "Мастер задумался, всматриваясь в нити судьбы..."
        await self._ws_send(
            MasterSpeech(narrator=text, dice_request=dice_request).model_dump()
        )

    # ── LLM call + trace ────────────────────────────────────────────────────

    async def _call_llm(
        self,
        system_prompt: str,
        user_msg: str,
        call_type: CallType,
    ) -> LLMResponse:
        """Call LLM, parse response, save trace, return structured result."""
        seq = await get_next_sequence(self.session_id)

        result = await self.llm.generate(system_prompt, user_msg)
        parsed = self.llm.parse_response(result.get("content", ""))

        # Save full trace
        await save_llm_trace(
            session_id=self.session_id,
            sequence=seq,
            call_type=call_type.value,
            system_prompt=system_prompt,
            user_context=user_msg,
            response_raw=result.get("raw_response", ""),
            response_parsed=json.dumps(parsed.model_dump(), ensure_ascii=False),
            duration_ms=result.get("duration_ms", 0),
            token_count=result.get("token_count", 0),
        )

        # Save world fact if present
        if parsed.world_update and parsed.world_update.summary:
            await save_world_fact(
                session_id=self.session_id,
                fact_type=parsed.world_update.fact_type.value,
                status=parsed.world_update.status.value,
                summary=parsed.world_update.summary,
                details=json.dumps(parsed.world_update.details, ensure_ascii=False),
            )

        return parsed

    # ── Dynamic context builder ─────────────────────────────────────────────

    async def _build_context(self) -> tuple[str, str]:
        """
        Build context_memory and world_lore for the current session.

        Returns:
            (context_memory_str, world_lore_str)
        """
        messages = await get_recent_messages(
            self.session_id, limit=settings.CONTEXT_MAX_MESSAGES
        )
        facts = await get_world_facts(self.session_id)

        context_memory = self.context_fmt.format_context_memory(messages)
        world_lore = self.context_fmt.format_world_lore(facts)

        return context_memory, world_lore

    async def _build_system_prompt(self) -> str:
        """Build full system prompt with base blocks + dynamic context."""
        context_memory, world_lore = await self._build_context()

        base = self.prompts.build_base_blocks()
        dynamic = self.prompts.build_dynamic_context(
            context_memory=context_memory,
            world_lore=world_lore,
        )
        return base + "\n\n" + dynamic

    # ── Public API: Greeting ────────────────────────────────────────────────

    async def start_greeting(self, player_name: str) -> None:
        """
        Execute the 2-step greeting ritual.

        Step 1 — ПРИГЛАШЕНИЕ (generic welcome, no name).
        Step 2 — ОБРАЩЕНИЕ (personal address by name, world creation).
        """
        self.log.info("Starting greeting ritual for: %s", player_name)

        # ── Step 1: Generic invitation ─────────────────────────────────────
        await self._think_started()

        system_prompt = self.prompts.build_greeting_system()
        user_msg = (
            "Новый гость прибыл. Проведи шаг 1 ритуала приветствия: "
            "ПРИГЛАШЕНИЕ. Назови мир, создай атмосферу, но НЕ используй "
            "имя гостя — ты его ещё не знаешь."
        )

        parsed = await self._call_llm(system_prompt, user_msg, CallType.GREETING)
        await save_message(self.session_id, "master", "narrative", parsed.narrator)

        await self._think_stopped()
        await self._narrate(parsed.narrator)

        # ── Step 2: Personal greeting by name ──────────────────────────────
        await self._think_started()

        # Reuse same system prompt; user_msg introduces the name
        user_msg = self.prompts.build_greeting_user_message(player_name)

        parsed = await self._call_llm(system_prompt, user_msg, CallType.GREETING)
        await save_message(self.session_id, "master", "narrative", parsed.narrator)

        await self._think_stopped()
        await self._narrate(parsed.narrator)

        self.log.info("Greeting ritual complete for: %s", player_name)

    # ── Public API: Player Input ────────────────────────────────────────────

    async def handle_player_input(self, content: str) -> None:
        """
        Process a player action/message.

        This is the FIRST LLM pass:
        - Narrate what happens
        - Optionally request a dice roll (<dice_request> tag)
        - Extract world facts
        """
        self.log.info("Player input: %s", content[:100])

        await self._think_started()

        system_prompt = await self._build_system_prompt()
        user_msg = self.prompts.build_player_turn(content)

        parsed = await self._call_llm(system_prompt, user_msg, CallType.FIRST_PASS)
        await save_message(self.session_id, "master", "narrative", parsed.narrator)

        # Handle dice request
        dice_request_dict: dict[str, Any] | None = None
        if parsed.dice_request and parsed.dice_request.skill:
            dice_request_dict = parsed.dice_request.model_dump()
            self._pending_dice_request_id = parsed.dice_request.request_id
            # Dice request is embedded in MasterSpeech.dice_request below

        await self._think_stopped()
        await self._narrate(parsed.narrator, dice_request=dice_request_dict)

    # ── Public API: Dice Result ─────────────────────────────────────────────

    async def handle_dice_result(
        self, request_id: str, roll: int, modifier: int = 0
    ) -> None:
        """
        Process a dice roll result from the client.

        This is the SECOND LLM pass:
        - Narrate the outcome with the dice result
        - Determine success/failure
        - Extract world consequences
        """
        total = roll + modifier
        self.log.info(
            "Dice result: request_id=%s roll=%d mod=%d total=%d",
            request_id, roll, modifier, total,
        )

        # Reset pending dice request
        self._pending_dice_request_id = None

        # Save dice result as system message
        await save_message(
            self.session_id,
            "system",
            "dice_result",
            f"Бросок d20: {roll} + {modifier} = {total} (request_id: {request_id})",
        )

        await self._think_started()

        system_prompt = await self._build_system_prompt()
        user_msg = (
            f"РЕЗУЛЬТАТ БРОСКА (request_id: {request_id}):\n"
            f"d20 = {roll}, модификатор = {modifier}, ИТОГО = {total}.\n\n"
            "Опиши результат проверки с учётом броска. "
            "Если выпало 20 — критический успех (опиши особенно эффектно). "
            "Если выпало 1 — критический провал (драматично). "
            "Сравни итог с DC проверки и опиши исход."
        )

        parsed = await self._call_llm(
            system_prompt, user_msg, CallType.DICE_SECOND_PASS
        )
        await save_message(self.session_id, "master", "narrative", parsed.narrator)

        await self._think_stopped()
        await self._narrate(parsed.narrator)