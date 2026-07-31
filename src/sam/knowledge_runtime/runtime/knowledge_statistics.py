"""Knowledge Statistics — statistik knowledge (Sprint 183)."""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.knowledge_registry import KnowledgeRegistry


@dataclass(frozen=True)
class KnowledgeStatistics:
    """Statistik knowledge (immutable)."""
    total: int = 0
    with_capability: int = 0
    with_contract: int = 0
    external_calls: int = 0


class KnowledgeStatisticsCollector:
    """Collector statistik. Read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def collect(self) -> KnowledgeStatistics:
        total = self._registry.count()
        with_cap = sum(1 for i in self._registry.list_ids()
                       if self._registry.get_capabilities(i))
        with_contract = sum(1 for i in self._registry.list_ids()
                            if self._registry.get_contract(i))
        return KnowledgeStatistics(
            total=total,
            with_capability=with_cap,
            with_contract=with_contract,
            external_calls=0,
        )
