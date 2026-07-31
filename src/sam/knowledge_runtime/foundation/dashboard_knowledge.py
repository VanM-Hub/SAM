"""Dashboard Knowledge Bridge — 5 ExecutionCards (Sprint 180)."""
from __future__ import annotations

from .knowledge_registry import KnowledgeRegistry
from ..dashboard.knowledge_dashboard import ExecutionCard


class DashboardKnowledgeBridge:
    """Bridge dashboard — 5 kartu untuk knowledge foundation."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def cards(self):
        n = self._registry.count()
        return [
            ExecutionCard("knowledge.foundation", "knowledge", "ready",
                          f"{n} knowledge(s) registered", "knowledge registry", "ready"),
            ExecutionCard("knowledge.descriptor", "knowledge", "ready",
                          "descriptors stored", "registry query", "ready"),
            ExecutionCard("knowledge.capability", "knowledge", "ready",
                          "capabilities attached", "registry query", "ready"),
            ExecutionCard("knowledge.contract", "knowledge", "ready",
                          "contracts attached", "registry query", "ready"),
            ExecutionCard("knowledge.metadata", "knowledge", "ready",
                          "metadata attached", "registry query", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
