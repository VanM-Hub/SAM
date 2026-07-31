"""Dashboard Model Bridge — 5 ExecutionCards (Sprint 173)."""
from __future__ import annotations

from ..dashboard.memory_dashboard import ExecutionCard


class DashboardModelBridge:
    """Bridge dashboard — 5 kartu untuk memory model."""

    def cards(self):
        return [
            ExecutionCard("model.record", "model", "ready",
                          "record model", "memory model", "ready"),
            ExecutionCard("model.entry", "model", "ready",
                          "entry model", "memory model", "ready"),
            ExecutionCard("model.reference", "model", "ready",
                          "reference model", "memory model", "ready"),
            ExecutionCard("model.scope", "model", "ready",
                          "scope model", "memory model", "ready"),
            ExecutionCard("model.tag", "model", "ready",
                          "tag model", "memory model", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
