"""Dashboard Coordinator Bridge — 5 ExecutionCards (Sprint 160).

Agent Runtime — dashboard bridge read-only.
"""
from __future__ import annotations

from .runtime_registry import RuntimeRegistry
from ..dashboard.agent_dashboard import ExecutionCard


class DashboardCoordinatorBridge:
    """Bridge dashboard — 5 kartu untuk runtime coordinator."""

    def __init__(self, registry: RuntimeRegistry) -> None:
        self._registry = registry

    def cards(self):
        n = self._registry.count()
        return [
            ExecutionCard("coordinator.registry", "coordinator", "ready",
                          f"{n} runtime(s) registered", "runtime registry", "ready"),
            ExecutionCard("coordinator.next", "coordinator", "ready",
                          "determines next runtime", "no execution", "ready"),
            ExecutionCard("coordinator.queue", "coordinator", "ready",
                          "runtime queue tracked", "deterministic", "ready"),
            ExecutionCard("coordinator.no_call", "coordinator", "ready",
                          "does not call runtimes", "preview-only", "ready"),
            ExecutionCard("coordinator.preview", "coordinator", "ready",
                          "preview-only coordination", "no approval", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
