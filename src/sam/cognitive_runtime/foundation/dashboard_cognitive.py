"""Dashboard Cognitive Bridge — 5 ExecutionCards (Sprint 188)."""
from __future__ import annotations

from ..dashboard import ExecutionCard
from .cognitive_registry import CognitiveRegistry


class DashboardCognitiveBridge:
    """Bridge dashboard — 5 kartu untuk fondasi kognitif."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def cards(self):
        n = self._registry.count()
        verdict = "ready" if n > 0 else "empty"
        return [
            ExecutionCard("fd.foundation", "foundation", verdict,
                          f"{n} cognitive descriptor(s)", "cognitive foundation", verdict),
            ExecutionCard("fd.descriptor", "foundation", "ready",
                          "CognitiveDescriptor frozen", "deterministic", "ready"),
            ExecutionCard("fd.capability", "foundation", "ready",
                          "CognitiveCapability frozen", "no-inference", "ready"),
            ExecutionCard("fd.contract", "foundation", "ready",
                          "CognitiveContract preview-only", "preview", "ready"),
            ExecutionCard("fd.metadata", "foundation", "ready",
                          "CognitiveMetadata version 19.0.0", "read-only", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
