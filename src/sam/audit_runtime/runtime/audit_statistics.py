"""Audit Statistics — statistik audit (Sprint 215)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.audit_registry import AuditRegistry


@dataclass(frozen=True)
class AuditStatistics:
    """Statistik immutable."""
    total: int = 0
    per_category: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "per_category", dict(self.per_category))


class AuditStatisticsCollector:
    """Kolektor statistik audit read-only."""

    def collect(self, registry: AuditRegistry) -> AuditStatistics:
        per = {}
        for a in registry.all_entries():
            per[a.category] = per.get(a.category, 0) + 1
        return AuditStatistics(total=registry.count(), per_category=per)
