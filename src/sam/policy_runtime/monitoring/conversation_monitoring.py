"""Conversation Monitoring Bridge — query read-only (Sprint 209)."""
from __future__ import annotations

from ..foundation.policy_registry import PolicyRegistry
from .policy_monitor import PolicyMonitor
from .policy_metrics import PolicyMetricsCollector
from .policy_health import PolicyHealthCheck
from .policy_report import PolicyReporter


class ConversationMonitoringBridge:
    """Bridge conversation — status pemantauan policy read-only."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry
        self._monitor = PolicyMonitor(registry)
        self._metrics = PolicyMetricsCollector(registry)
        self._health = PolicyHealthCheck(registry)
        self._reporter = PolicyReporter(registry)

    def health(self, policy_id: str) -> bool:
        return self._monitor.status(policy_id).healthy

    def summary(self) -> dict:
        rep = self._reporter.report()
        return {"total": rep.total, "healthy": rep.healthy, "external_calls": 0}

    def metrics(self) -> dict:
        m = self._metrics.collect()
        return {"total": m.total, "external_calls": m.external_calls}
