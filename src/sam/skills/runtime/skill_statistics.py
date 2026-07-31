"""Skill Statistics — statistik skill runtime (Sprint 167).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.skill_registry import SkillRegistry


@dataclass(frozen=True)
class SkillStatistics:
    """Statistik skill (immutable)."""
    total: int = 0
    with_capability: int = 0
    with_contract: int = 0
    external_calls: int = 0


class SkillStatisticsCollector:
    """Collector statistik. Read-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def collect(self) -> SkillStatistics:
        total = self._registry.count()
        with_cap = sum(1 for i in self._registry.list_ids()
                       if self._registry.get_capabilities(i))
        with_contract = sum(1 for i in self._registry.list_ids()
                            if self._registry.get_contract(i))
        return SkillStatistics(
            total=total,
            with_capability=with_cap,
            with_contract=with_contract,
            external_calls=0,
        )
