"""Dashboard Model Bridge — 5 ExecutionCards (Sprint 181)."""
from __future__ import annotations

from ..dashboard.knowledge_dashboard import ExecutionCard


class DashboardModelBridge:
    """Bridge dashboard — 5 kartu untuk knowledge model."""

    def cards(self):
        return [
            ExecutionCard("model.record", "model", "ready",
                          "record model", "knowledge model", "ready"),
            ExecutionCard("model.fact", "model", "ready",
                          "fact model", "knowledge model", "ready"),
            ExecutionCard("model.relation", "model", "ready",
                          "relation model", "knowledge model", "ready"),
            ExecutionCard("model.context", "model", "ready",
                          "context model", "knowledge model", "ready"),
            ExecutionCard("model.tag", "model", "ready",
                          "tag model", "knowledge model", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
