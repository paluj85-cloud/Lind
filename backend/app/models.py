"""Pydantic models for API requests, responses, and internal data structures."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────


class SessionStatus(str, Enum):
    ACTIVE = "active"
    FINISHED = "finished"


class MessageRole(str, Enum):
    PLAYER = "player"
    MASTER = "master"
    SYSTEM = "system"


class MessageType(str, Enum):
    SAY = "say"
    DO = "do"
    NARRATIVE = "narrative"
    DICE_REQUEST = "dice_request"
    DICE_RESULT = "dice_result"
    SYSTEM = "system"


class FactStatus(str, Enum):
    ABSOLUTE_TRUTH = "ABSOLUTE_TRUTH"
    RUMOR = "RUMOR"
    LIE = "LIE"


class FactType(str, Enum):
    ENTITY_CHANGE = "entity_change"
    LOCATION_CHANGE = "location_change"
    EVENT = "event"
    ITEM_CHANGE = "item_change"


class CallType(str, Enum):
    FIRST_PASS = "first_pass"
    DICE_SECOND_PASS = "dice_second_pass"
    GREETING = "greeting"
    WORLD_CREATION = "world_creation"


# ── Request Models ───────────────────────────────────────────────────────────


class PlayerMessage(BaseModel):
    """Message sent from the player via WebSocket."""

    type: str = "player_message"
    action_type: MessageType = MessageType.SAY
    content: str = ""


class DiceCheckResult(BaseModel):
    """Result of a d20 skill check — returned by game/dice.py."""

    request_id: str
    skill: str
    dc: int
    roll: int
    modifier: int = 0
    total: int = 0
    success: bool = False
    critical_success: bool = False  # natural 20
    critical_failure: bool = False  # natural 1
    narrative_hint: str = ""  # suggested outcome tone for LLM


# ── Internal / Game Loop Models ──────────────────────────────────────────────


class DiceRequest(BaseModel):
    """Parsed <dice_request> from LLM response."""

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    skill: str = ""
    dc: int = 0  # Difficulty Class
    reason: str = ""


class WorldUpdate(BaseModel):
    """Parsed <state_update> from LLM response."""

    fact_type: FactType = FactType.EVENT
    status: FactStatus = FactStatus.ABSOLUTE_TRUTH
    summary: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Structured response from the LLM after parsing."""

    narrator: str = ""
    world_update: WorldUpdate | None = None
    dice_request: DiceRequest | None = None
    raw_response: str = ""


# ── WS Protocol Messages (server → client) ───────────────────────────────────


class WSMessage(BaseModel):
    """Base WebSocket message from server to client."""

    type: str


class MasterThinking(WSMessage):
    type: str = "master_thinking"
    status: str  # "started" | "stopped"


class MasterSpeech(WSMessage):
    type: str = "master_speech"
    narrator: str
    dice_request: dict[str, Any] | None = None


class DiceRollRequest(WSMessage):
    type: str = "dice_roll_request"
    request_id: str
    skill: str
    dc: int
    reason: str


class SessionCreated(WSMessage):
    type: str = "session_created"
    session_id: str


# ── Helper ───────────────────────────────────────────────────────────────────


def utc_now() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()