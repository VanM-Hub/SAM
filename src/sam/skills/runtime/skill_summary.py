"""Skill Summary — ringkasan skill runtime (Sprint 167).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.skill_registry import SkillRegistry


@dataclass(frozen=True)
class SkillSummary:
    """Ringkasan skill runtime (immutable)."""
    version: str = "1.0.0"
    total_skills: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)
    external_calls: int = 0


class SkillSummarizer:
    """Summarizer skill. Read-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def summary(self) -> SkillSummary:
        s = self._registry.summary()
        return SkillSummary(
            version="1.0.0",
            total_skills=s.total,
            by_category=s.by_category,
            external_calls=0,
        )
