"""Dashboard Runtime Bridge — 5 ExecutionCards (Sprint 191)."""
from __future__ import annotations

from ..dashboard import ExecutionCard
from ..foundation.cognitive_registry import CognitiveRegistry
from .cognitive_runtime import CognitiveRuntime
from .cognitive_pipeline import CognitivePipeline
from .cognitive_engine import CognitiveEngine


class DashboardRuntimeBridge:
    """Bridge dashboard — 5 kartu untuk runtime kognitif."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry
        self._runtime = CognitiveRuntime(registry)
        self._pipeline = CognitivePipeline(registry)

    def cards(self):
        n = self._registry.count()
        verdict = "ready" if n > 0 else "empty"
        return [
            ExecutionCard("rt.runtime", "runtime", verdict,
                          f"{n} cognitive(s) runnable", "cognitive runtime", verdict),
            ExecutionCard("rt.pipeline", "runtime", "ready",
                          "Descriptor->Context->Snapshot->Workspace->Preview",
                          "pipeline", "ready"),
            ExecutionCard("rt.preview", "runtime", "ready",
                          "no inference, external_calls=0", "preview", "ready"),
            ExecutionCard("rt.engine", "runtime", "ready",
                          "engine: not LLM, not AI, deterministic", "engine", "ready"),
            ExecutionCard("rt.summary", "runtime", "ready",
                          "CognitiveSummarizer deterministic", "summary", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
