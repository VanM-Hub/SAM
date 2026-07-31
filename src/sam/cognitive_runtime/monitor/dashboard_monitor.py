"""Dashboard Monitor Bridge — 5 ExecutionCards (Sprint 193)."""
from __future__ import annotations

from ..dashboard import ExecutionCard
from ..foundation.cognitive_registry import CognitiveRegistry
from .cognitive_monitor import CognitiveMonitor
from .cognitive_report import CognitiveReporter


class DashboardMonitorBridge:
    """Bridge dashboard — 5 kartu untuk pemantauan kognitif."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry
        self._monitor = CognitiveMonitor(registry)
        self._reporter = CognitiveReporter(registry)

    def cards(self):
        rep = self._reporter.report()
        verdict = "ready" if rep.healthy > 0 else "empty"
        return [
            ExecutionCard("mo.total", "monitor", verdict,
                          f"{rep.total} cognitive(s) tracked", "health", verdict),
            ExecutionCard("mo.metrics", "monitor", "ready",
                          f"external_calls={rep.external_calls}", "metrics", "ready"),
            ExecutionCard("mo.health", "monitor", "ready",
                          "CognitiveHealthCheck deterministic", "health", "ready"),
            ExecutionCard("mo.snapshot", "monitor", "ready",
                          "CognitiveSnapshot report ready", "snapshot", "ready"),
            ExecutionCard("mo.preview", "monitor", "ready",
                          "monitor: read-only, no inference", "preview", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
