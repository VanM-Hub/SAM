"""Memory Statistics — statistik memori (Sprint 175)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

from ..foundation.memory_registry import MemoryRegistry


@dataclass(frozen=True)
class MemoryStatistics:
    """Statistik memori (immutable)."""
    total: int = 0
    with_capability: int = 0
    with_contract: int = 0
    external_calls: int = 0


class MemoryStatisticsCollector:
    """Collector statistik. Read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def collect(self) -> MemoryStatistics:
        total = self._registry.count()
        with_cap = sum(1 for i in self._registry.list_ids()
                       if self._registry.get_capabilities(i))
        with_contract = sum(1 for i in self._registry.list_ids()
                            if self._registry.get_contract(i))
        return MemoryStatistics(
            total=total,
            with_capability=with_cap,
            with_contract=with_contract,
            external_calls=0,
        )
