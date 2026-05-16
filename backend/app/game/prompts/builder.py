"""PromptBuilder — assembles system and user prompts for Exis."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.game.prompts.blocks import (
    BLOCK_1_ПРОБУЖДЕНИЕ,
    BLOCK_2_КУЗНИЦА,
    BLOCK_3_ДВА_СВИТКА,
    BLOCK_4_СТРАЖ,
    BLOCK_5_ЗАКОНЫ,
    BLOCK_6_ПРОТОКОЛ,
    ФИНАЛ,
    JSON_FORMAT_INSTRUCTION,
    GREETING_PROMPT,
)


class PromptBuilder:
    """Builds the full system prompt for Exis with dynamic context."""

    @staticmethod
    def build_base_blocks() -> str:
        """Return the 6 immutable blocks + finale + format."""
        return "\n\n".join([
            "# БЛОК 1: ПРОБУЖДЕНИЕ",
            BLOCK_1_ПРОБУЖДЕНИЕ,
            "# БЛОК 2: КУЗНИЦА",
            BLOCK_2_КУЗНИЦА,
            "# БЛОК 3: ДВА СВИТКА",
            BLOCK_3_ДВА_СВИТКА,
            "# БЛОК 4: СТРАЖ",
            BLOCK_4_СТРАЖ,
            "# БЛОК 5: ЗАКОНЫ МИРОЗДАНИЯ",
            BLOCK_5_ЗАКОНЫ,
            "# БЛОК 6: ПРОТОКОЛ ВЫЗОВА",
            BLOCK_6_ПРОТОКОЛ,
            "# ФИНАЛ",
            ФИНАЛ,
            "# ФОРМАТ ОТВЕТА",
            JSON_FORMAT_INSTRUCTION,
        ])

    @staticmethod
    def build_dynamic_context(
        player_name: str = "",
        world_name: str = "Lind",
        reveal_level: int = 0,
        context_memory: str = "",
        world_lore: str = "",
    ) -> str:
        """Build the dynamic context block with current game state."""
        parts = []

        parts.append("## ТЕКУЩИЙ КОНТЕКСТ")
        parts.append(f"Мир: {world_name}")
        if player_name:
            parts.append(f"Игрок (Демиург): {player_name}")
        parts.append(f"Уровень Откровения: {reveal_level}")
        parts.append("")

        if context_memory:
            parts.append("## КОНТЕКСТ ПАМЯТИ (последние сообщения)")
            parts.append(context_memory)
            parts.append("")

        if world_lore:
            parts.append("## МИРОВОЙ ЛОР")
            parts.append(world_lore)
            parts.append("")

        return "\n".join(parts)

    @staticmethod
    def build_greeting_system() -> str:
        """Build the system prompt for the greeting ritual."""
        return "\n\n".join([
            "# БЛОК 1: ПРОБУЖДЕНИЕ",
            BLOCK_1_ПРОБУЖДЕНИЕ,
            "# БЛОК 2: КУЗНИЦА",
            BLOCK_2_КУЗНИЦА,
            "# РИТУАЛ ПЕРВОГО КОНТАКТА",
            GREETING_PROMPT,
            "# ФОРМАТ ОТВЕТА",
            JSON_FORMAT_INSTRUCTION,
        ])

    @staticmethod
    def build_greeting_user_message(
        player_name: str,
    ) -> str:
        """Build the user prompt after the player gave their name."""
        return (
            f"Игрок назвал своё имя: {player_name}\n\n"
            "Теперь проведи шаги 2-5 ритуала: "
            "Пророчество, Рождение Анимы, Первый Взгляд, Свобода."
        )

    @staticmethod
    def build_player_turn(
        player_action: str,
        dice_result: str = "",
    ) -> str:
        """Build the user prompt for a player's turn."""
        parts = [f"ИГРОК: {player_action}"]
        if dice_result:
            parts.append(f"РЕЗУЛЬТАТ БРОСКА: {dice_result}")
        return "\n".join(parts)


# Singleton
_builder: PromptBuilder | None = None


def get_prompt_builder() -> PromptBuilder:
    """Get or create the prompt builder singleton."""
    global _builder
    if _builder is None:
        _builder = PromptBuilder()
    return _builder