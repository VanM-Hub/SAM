"""Dashboard Memory Bridge — 5 ExecutionCards (Sprint 172)."""
from __future__ import annotations

from .memory_registry import MemoryRegistry
from ..dashboard.memory_dashboard import ExecutionCard


class DashboardMemoryBridge:
    """Bridge dashboard — 5 kartu untuk memory foundation."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def cards(self):
        n = self._registry.count()
        return [
            ExecutionCard("memory.foundation", "memory", "ready",
                          f"{n} memory(s) registered", "memory registry", "ready"),
            ExecutionCard("memory.descriptor", "memory", "ready",
                          "descriptors stored", "registry query", "ready"),
            ExecutionCard("memory.capability", "memory", "ready",
                          "capabilities attached", "registry query", "ready"),
            ExecutionCard("memory.contract", "memory", "ready",
                          "contracts attached", "registry query", "ready"),
            ExecutionCard("memory.metadata", "memory", "ready",
                          "metadata attached", "registry query", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
