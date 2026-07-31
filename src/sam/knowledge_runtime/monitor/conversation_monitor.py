"""Conversation Monitor Bridge — query read-only (Sprint 185)."""
from __future__ import annotations

from .knowledge_monitor import KnowledgeMonitor
from .knowledge_report import KnowledgeReporter


class ConversationMonitorBridge:
    """Bridge conversation — ringkasan monitoring knowledge read-only."""

    def __init__(self, monitor: KnowledgeMonitor, reporter: KnowledgeReporter = None) -> None:
        self._monitor = monitor
        self._reporter = reporter

    def health(self, knowledge_id: str) -> bool:
        return self._monitor.status(knowledge_id).healthy

    def summary(self) -> dict:
        if self._reporter is None:
            return {"total": 0}
        r = self._reporter.report()
        return {"total": r.total, "healthy": r.healthy,
                "external_calls": r.external_calls}
