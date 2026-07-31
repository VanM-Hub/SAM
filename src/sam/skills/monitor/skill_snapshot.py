"""Skill Snapshot — snapshot skill (Sprint 169).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.skill_registry import SkillRegistry


@dataclass(frozen=True)
class SkillSnapshot:
    """Snapshot skill (immutable)."""
    skill_id: str = ""
    total: int = 0
    categories: Dict[str, int] = field(default_factory=dict)


class SkillSnapshotter:
    """Pembuat snapshot skill. Read-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def snapshot(self) -> SkillSnapshot:
        s = self._registry.summary()
        return SkillSnapshot(
            skill_id="all", total=s.total, categories=s.by_category,
        )
