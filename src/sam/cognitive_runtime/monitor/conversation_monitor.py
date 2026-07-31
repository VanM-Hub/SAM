"""Conversation Monitor Bridge — query read-only (Sprint 193)."""
from __future__ import annotations

from ..foundation.cognitive_registry import CognitiveRegistry
from .cognitive_monitor import CognitiveMonitor
from .cognitive_metrics import CognitiveMetricsCollector
from .cognitive_health import CognitiveHealthCheck
from .cognitive_report import CognitiveReporter


class ConversationMonitorBridge:
    """Bridge conversation — status pemantauan kognitif read-only."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry
        self._monitor = CognitiveMonitor(registry)
        self._metrics = CognitiveMetricsCollector(registry)
        self._health = CognitiveHealthCheck(registry)
        self._reporter = CognitiveReporter(registry)

    def health(self, cognitive_id: str) -> bool:
        return self._monitor.status(cognitive_id).healthy

    def summary(self) -> dict:
        rep = self._reporter.report()
        return {"total": rep.total, "healthy": rep.healthy, "external_calls": 0}

    def metrics(self) -> dict:
        m = self._metrics.collect()
        return {"total": m.total, "external_calls": m.external_calls}
