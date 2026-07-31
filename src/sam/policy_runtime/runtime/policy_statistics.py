"""Policy Statistics — statistika runtime policy (Sprint 207)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.policy_registry import PolicyRegistry


@dataclass(frozen=True)
class PolicyStatisticsItem:
    """Statistik per unit (immutable)."""
    policy_id: str = ""
    registered: bool = False


@dataclass(frozen=True)
class PolicyStatistics:
    """Statistik policy (immutable)."""
    total: int = 0
    registered: int = 0
    items: List[PolicyStatisticsItem] = field(default_factory=list)


class PolicyStatisticsCollector:
    """Collector statistik. Read-only."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def collect(self) -> PolicyStatistics:
        descs = self._registry.all()
        items = [
            PolicyStatisticsItem(policy_id=d.id, registered=True)
            for d in descs
        ]
        return PolicyStatistics(total=len(items), registered=len(items), items=items)
