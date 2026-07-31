"""Conversation Monitoring Bridge — query read-only (Sprint 201)."""
from __future__ import annotations

from ..foundation.workflow_registry import WorkflowRegistry
from .workflow_monitor import WorkflowMonitor
from .workflow_metrics import WorkflowMetricsCollector
from .workflow_health import WorkflowHealthCheck
from .workflow_report import WorkflowReporter


class ConversationMonitoringBridge:
    """Bridge conversation — status pemantauan workflow read-only."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry
        self._monitor = WorkflowMonitor(registry)
        self._metrics = WorkflowMetricsCollector(registry)
        self._health = WorkflowHealthCheck(registry)
        self._reporter = WorkflowReporter(registry)

    def health(self, workflow_id: str) -> bool:
        return self._monitor.status(workflow_id).healthy

    def summary(self) -> dict:
        rep = self._reporter.report()
        return {"total": rep.total, "healthy": rep.healthy, "external_calls": 0}

    def metrics(self) -> dict:
        m = self._metrics.collect()
        return {"total": m.total, "external_calls": m.external_calls}
