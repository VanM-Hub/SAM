"""Conversation Monitor Bridge — query read-only (Sprint 177)."""
from __future__ import annotations

from .memory_monitor import MemoryMonitor
from .memory_report import MemoryReporter


class ConversationMonitorBridge:
    """Bridge conversation — ringkasan monitoring memori read-only."""

    def __init__(self, monitor: MemoryMonitor, reporter: MemoryReporter = None) -> None:
        self._monitor = monitor
        self._reporter = reporter

    def health(self, memory_id: str) -> bool:
        return self._monitor.status(memory_id).healthy

    def summary(self) -> dict:
        if self._reporter is None:
            return {"total": 0}
        r = self._reporter.report()
        return {"total": r.total, "healthy": r.healthy,
                "external_calls": r.external_calls}
