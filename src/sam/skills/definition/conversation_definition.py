"""Conversation Definition Bridge — query read-only (Sprint 165)."""
from __future__ import annotations

from .skill_definition import SkillDefinition
from .skill_validator import SkillValidator


class ConversationDefinitionBridge:
    """Bridge conversation — ringkasan definisi skill read-only."""

    def __init__(self, definition: SkillDefinition = None) -> None:
        self._definition = definition
        self._validator = SkillValidator()

    def summary(self) -> dict:
        if self._definition is None:
            return {"has_definition": False}
        return {
            "has_definition": True,
            "skill_id": self._definition.skill_id,
            "inputs": self._definition.input_count,
            "outputs": self._definition.output_count,
        }

    def validity(self) -> dict:
        if self._definition is None:
            return {"valid": False, "issues": ["no definition"]}
        v = self._validator.validate(self._definition)
        return {"valid": v.valid, "issues": v.issues}
