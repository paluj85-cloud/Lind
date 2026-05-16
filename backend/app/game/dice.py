"""Dice mechanics — d20 check resolution."""

from __future__ import annotations

import random

from backend.app.models import DiceCheckResult


def roll_d20() -> int:
    """Roll a 20-sided die."""
    return random.randint(1, 20)


def check_d20(
    request_id: str = "",
    skill: str = "",
    dc: int = 15,
    modifier: int = 0,
    roll: int | None = None,
) -> DiceCheckResult:
    """
    Resolve a d20 skill check.

    Returns a DiceCheckResult Pydantic model with:
        roll: the raw d20 roll
        modifier: the modifier applied
        total: roll + modifier
        dc: the difficulty class
        success: True if total >= dc
        critical_success: natural 20
        critical_failure: natural 1
        narrative_hint: suggested outcome tone for LLM
    """
    roll_value = roll if roll is not None else roll_d20()
    total = roll_value + modifier
    success = total >= dc
    critical_success = roll_value == 20
    critical_failure = roll_value == 1

    # Build narrative hint
    if critical_success:
        hint = "Critical success! Описать максимально эффектно, результат превосходит ожидания."
    elif critical_failure:
        hint = "Critical failure! Описать драматичный провал с неожиданными последствиями."
    elif success:
        hint = "Успех. Действие удалось, описать уверенный результат."
    else:
        hint = "Провал. Действие не удалось, описать последствия неудачи."

    return DiceCheckResult(
        request_id=request_id,
        skill=skill,
        dc=dc,
        roll=roll_value,
        modifier=modifier,
        total=total,
        success=success,
        critical_success=critical_success,
        critical_failure=critical_failure,
        narrative_hint=hint,
    )