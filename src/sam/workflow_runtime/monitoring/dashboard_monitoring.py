"""Dashboard Monitoring Bridge — 5 WorkflowCards (Sprint 201)."""
from __future__ import annotations

from ..dashboard import WorkflowCard
from ..foundation.workflow_registry import WorkflowRegistry
from .workflow_report import WorkflowReporter


class DashboardMonitoringBridge:
    """Bridge dashboard — 5 kartu untuk pemantauan workflow."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry
        self._reporter = WorkflowReporter(registry)

    def cards(self):
        rep = self._reporter.report()
        verdict = "ready" if rep.healthy > 0 else "empty"
        return [
            WorkflowCard("mo.total", "monitor", verdict,
                         f"{rep.total} workflow(s) tracked", "health", verdict),
            WorkflowCard("mo.metrics", "monitor", "ready",
                         f"external_calls={rep.external_calls}", "metrics", "ready"),
            WorkflowCard("mo.health", "monitor", "ready",
                         "WorkflowHealthCheck deterministic", "health", "ready"),
            WorkflowCard("mo.snapshot", "monitor", "ready",
                         "WorkflowSnapshot report ready", "snapshot", "ready"),
            WorkflowCard("mo.preview", "monitor", "ready",
                         "monitor: read-only, no inference", "preview", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
