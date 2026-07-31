"""Dashboard Monitoring Bridge — 5 PolicyCards (Sprint 209)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from ..foundation.policy_registry import PolicyRegistry
from .policy_report import PolicyReporter


class DashboardMonitoringBridge:
    """Bridge dashboard — 5 kartu untuk pemantauan policy."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry
        self._reporter = PolicyReporter(registry)

    def cards(self):
        rep = self._reporter.report()
        verdict = "ready" if rep.healthy > 0 else "empty"
        return [
            PolicyCard("mo.total", "monitor", verdict,
                       f"{rep.total} policy(s) tracked", "health", verdict),
            PolicyCard("mo.metrics", "monitor", "ready",
                       f"external_calls={rep.external_calls}", "metrics", "ready"),
            PolicyCard("mo.health", "monitor", "ready",
                       "PolicyHealthCheck deterministic", "health", "ready"),
            PolicyCard("mo.snapshot", "monitor", "ready",
                       "PolicySnapshot report ready", "snapshot", "ready"),
            PolicyCard("mo.preview", "monitor", "ready",
                       "monitor: read-only, no inference", "preview", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
