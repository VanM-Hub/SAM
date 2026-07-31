"""Conversation Builder Bridge — query read-only (Sprint 166)."""
from __future__ import annotations

from .skill_builder import SkillBuilder


class ConversationBuilderBridge:
    """Bridge conversation — ringkasan builder skill read-only."""

    def __init__(self, builder: SkillBuilder = None) -> None:
        self._builder = builder or SkillBuilder()

    def summary(self, skill_id: str) -> dict:
        res = self._builder.build(skill_id)
        return {"valid": res.valid, "reason": res.reason}

    def describe_builder(self) -> str:
        return "skill builder (build-only, no execution)"
