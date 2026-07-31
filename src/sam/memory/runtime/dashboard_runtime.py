"""Dashboard Runtime Bridge — 5 ExecutionCards (Sprint 175)."""
from __future__ import annotations

from .memory_runtime import MemoryRuntime
from ..dashboard.memory_dashboard import ExecutionCard


class DashboardRuntimeBridge:
    """Bridge dashboard — 5 kartu untuk memory runtime."""

    def __init__(self, runtime: MemoryRuntime) -> None:
        self._runtime = runtime

    def cards(self):
        n = self._runtime.registry.count()
        return [
            ExecutionCard("runtime.engine", "runtime", "ready",
                          "memory runtime engine", "preview-only", "ready"),
            ExecutionCard("runtime.pipeline", "runtime", "ready",
                          "Descriptor->Record->Builder->Snapshot->Preview",
                          "pipeline", "ready"),
            ExecutionCard("runtime.registry", "runtime", "ready",
                          f"{n} memory(s) in registry", "memory runtime", "ready"),
            ExecutionCard("runtime.no_store", "runtime", "ready",
                          "no filesystem/database write", "preview", "ready"),
            ExecutionCard("runtime.deterministic", "runtime", "ready",
                          "synchronous & deterministic", "engine", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
