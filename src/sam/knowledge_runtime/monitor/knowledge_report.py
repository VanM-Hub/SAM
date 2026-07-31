"""Knowledge Report — laporan knowledge (Sprint 185).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.knowledge_registry import KnowledgeRegistry
from .knowledge_monitor import KnowledgeMonitor


@dataclass(frozen=True)
class KnowledgeReport:
    """Laporan knowledge (immutable)."""
    total: int = 0
    healthy: int = 0
    unregistered: int = 0
    external_calls: int = 0


class KnowledgeReporter:
    """Reporter knowledge. Read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry
        self._monitor = KnowledgeMonitor(registry)

    def report(self) -> KnowledgeReport:
        statuses = self._monitor.all_status()
        healthy = sum(1 for s in statuses if s.healthy)
        unreg = sum(1 for s in statuses if not s.registered)
        return KnowledgeReport(
            total=len(statuses),
            healthy=healthy,
            unregistered=unreg,
            external_calls=0,
        )
