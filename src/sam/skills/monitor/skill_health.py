"""Skill Health — kesehatan skill (Sprint 169).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.skill_registry import SkillRegistry
from .skill_monitor import SkillMonitor


@dataclass(frozen=True)
class SkillHealth:
    """Kesehatan skill (immutable)."""
    healthy: bool = True
    total: int = 0
    healthy_skills: int = 0
    issues: List[str] = field(default_factory=list)


class SkillHealthCheck:
    """Health check skill. Read-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry
        self._monitor = SkillMonitor(registry)

    def check(self) -> SkillHealth:
        statuses = self._monitor.all_status()
        healthy = sum(1 for s in statuses if s.healthy)
        issues = [f"{s.skill_id} unregistered" for s in statuses if not s.registered]
        return SkillHealth(
            healthy=len(issues) == 0,
            total=len(statuses),
            healthy_skills=healthy,
            issues=issues,
        )
