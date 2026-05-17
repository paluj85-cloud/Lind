"""ContextFormatter — formats session memory and world lore for LLM context."""

from __future__ import annotations

from backend.app.config import settings


class ContextFormatter:
    """Formats dynamic context (recent messages + world facts) for prompts."""

    @staticmethod
    def format_context_memory(messages: list[dict]) -> str:
        """Format recent messages into a context memory string."""
        if not messages:
            return ""
        lines = []
        for msg in messages[-settings.CONTEXT_MAX_MESSAGES:]:
            # Skip system messages — they are internal, not for LLM context
            if msg.get("role") == "system":
                continue
            role_label = {
                "player": "🎮 ИГРОК",
                "master": "⚜ ЭКС-ИС",
            }.get(msg.get("role", ""), msg.get("role", "?"))
            content = msg.get("content", "")
            # Truncate long messages to avoid bloat
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"{role_label}: {content}")
        return "\n".join(lines)

    @staticmethod
    def format_world_lore(facts: list[dict]) -> str:
        """Format world facts into a world lore string."""
        if not facts:
            return ""
        lines = []
        for fact in facts:
            status = fact.get("status", "?")
            summary = fact.get("summary", "")
            ftype = fact.get("fact_type", "?")
            emoji = {
                "ABSOLUTE_TRUTH": "📜",
                "RUMOR": "💬",
                "LIE": "🗣️",
            }.get(status, "❓")
            lines.append(f"{emoji} [{ftype}] [{status}] {summary}")
        return "\n".join(lines)