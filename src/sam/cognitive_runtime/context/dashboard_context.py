"""Dashboard Context Bridge — 5 ExecutionCards (Sprint 189)."""
from __future__ import annotations

from ..dashboard import ExecutionCard
from .cognitive_context import CognitiveContext
from .cognitive_scope import CognitiveScope


class DashboardContextBridge:
    """Bridge dashboard — 5 kartu untuk konteks kognitif."""

    def cards(self, context: CognitiveContext = None):
        ctx = context or CognitiveContext()
        return [
            ExecutionCard("ctx.context", "context", "ready",
                          f"scope={ctx.scope}, entries={ctx.entry_count()}",
                          "cognitive context", "ready"),
            ExecutionCard("ctx.snapshot", "context", "ready",
                          "CognitiveSnapshot frozen", "snapshot", "ready"),
            ExecutionCard("ctx.scope", "context", "ready",
                          "CognitiveScope validated", "scope", "ready"),
            ExecutionCard("ctx.reference", "context", "ready",
                          "CognitiveReference read-only", "reference", "ready"),
            ExecutionCard("ctx.valid", "context", "ready",
                          "CognitiveValidator deterministic", "no-inference", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
