"""Dashboard Builder Bridge — 5 ExecutionCards (Sprint 182)."""
from __future__ import annotations

from .knowledge_builder import KnowledgeBuilder
from ..dashboard.knowledge_dashboard import ExecutionCard


class DashboardBuilderBridge:
    """Bridge dashboard — 5 kartu untuk knowledge builder."""

    def __init__(self, builder: KnowledgeBuilder = None) -> None:
        self._builder = builder or KnowledgeBuilder()

    def cards(self):
        return [
            ExecutionCard("build.descriptor", "builder", "ready",
                          "descriptor built from DTO", "knowledge builder", "ready"),
            ExecutionCard("build.record", "builder", "ready",
                          "record built from DTO", "knowledge builder", "ready"),
            ExecutionCard("build.fact", "builder", "ready",
                          "fact built", "knowledge builder", "ready"),
            ExecutionCard("build.relation", "builder", "ready",
                          "relation built", "knowledge builder", "ready"),
            ExecutionCard("build.no_infer", "builder", "ready",
                          "build-only, no inference, no store",
                          "knowledge builder", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
