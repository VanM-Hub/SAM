"""Skill Report — laporan skill (Sprint 169).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.skill_registry import SkillRegistry
from .skill_monitor import SkillMonitor


@dataclass(frozen=True)
class SkillReport:
    """Laporan skill (immutable)."""
    total: int = 0
    healthy: int = 0
    unregistered: int = 0
    external_calls: int = 0


class SkillReporter:
    """Reporter skill. Read-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry
        self._monitor = SkillMonitor(registry)

    def report(self) -> SkillReport:
        statuses = self._monitor.all_status()
        healthy = sum(1 for s in statuses if s.healthy)
        unreg = sum(1 for s in statuses if not s.registered)
        return SkillReport(
            total=len(statuses),
            healthy=healthy,
            unregistered=unreg,
            external_calls=0,
        )
