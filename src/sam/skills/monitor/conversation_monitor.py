"""Conversation Monitor Bridge — query read-only (Sprint 169)."""
from __future__ import annotations

from .skill_monitor import SkillMonitor
from .skill_report import SkillReporter


class ConversationMonitorBridge:
    """Bridge conversation — ringkasan monitoring skill read-only."""

    def __init__(self, monitor: SkillMonitor, reporter: SkillReporter = None) -> None:
        self._monitor = monitor
        self._reporter = reporter

    def health(self, skill_id: str) -> bool:
        return self._monitor.status(skill_id).healthy

    def summary(self) -> dict:
        if self._reporter is None:
            return {"total": 0}
        r = self._reporter.report()
        return {"total": r.total, "healthy": r.healthy,
                "external_calls": r.external_calls}
