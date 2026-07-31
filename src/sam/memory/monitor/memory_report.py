"""Memory Report — laporan memori (Sprint 177).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.memory_registry import MemoryRegistry
from .memory_monitor import MemoryMonitor


@dataclass(frozen=True)
class MemoryReport:
    """Laporan memori (immutable)."""
    total: int = 0
    healthy: int = 0
    unregistered: int = 0
    external_calls: int = 0


class MemoryReporter:
    """Reporter memori. Read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry
        self._monitor = MemoryMonitor(registry)

    def report(self) -> MemoryReport:
        statuses = self._monitor.all_status()
        healthy = sum(1 for s in statuses if s.healthy)
        unreg = sum(1 for s in statuses if not s.registered)
        return MemoryReport(
            total=len(statuses),
            healthy=healthy,
            unregistered=unreg,
            external_calls=0,
        )
