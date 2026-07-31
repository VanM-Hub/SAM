"""Dashboard Builder Bridge — 5 ExecutionCards (Sprint 174)."""
from __future__ import annotations

from .memory_builder import MemoryBuilder
from ..dashboard.memory_dashboard import ExecutionCard


class DashboardBuilderBridge:
    """Bridge dashboard — 5 kartu untuk memory builder."""

    def __init__(self, builder: MemoryBuilder = None) -> None:
        self._builder = builder or MemoryBuilder()

    def cards(self):
        return [
            ExecutionCard("build.descriptor", "builder", "ready",
                          "descriptor built from DTO", "memory builder", "ready"),
            ExecutionCard("build.record", "builder", "ready",
                          "record built from DTO", "memory builder", "ready"),
            ExecutionCard("build.context", "builder", "ready",
                          "context built", "memory builder", "ready"),
            ExecutionCard("build.snapshot", "builder", "ready",
                          "snapshot built", "memory builder", "ready"),
            ExecutionCard("build.no_store", "builder", "ready",
                          "build-only, no store", "memory builder", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
