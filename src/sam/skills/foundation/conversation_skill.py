"""Conversation Skill Bridge — query read-only (Sprint 164)."""
from __future__ import annotations

from .skill_registry import SkillRegistry


class ConversationSkillBridge:
    """Bridge conversation — ringkasan skill read-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def summary(self) -> dict:
        s = self._registry.summary()
        return {"total": s.total, "by_category": s.by_category}

    def registry(self) -> list:
        return self._registry.list_ids()

    def descriptor(self, skill_id: str) -> str:
        d = self._registry.find(skill_id)
        return d.name if d else f"skill {skill_id} not found"

    def metadata(self, skill_id: str) -> dict:
        m = self._registry.get_metadata(skill_id)
        if m is None:
            return {}
        return {"author": m.author, "tags": m.tags}

    def capability(self, skill_id: str) -> list:
        return [c.capability_id for c in self._registry.get_capabilities(skill_id)]
