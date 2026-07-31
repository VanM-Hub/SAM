"""Dashboard Runtime Bridge — 5 ExecutionCards (Sprint 183)."""
from __future__ import annotations

from .knowledge_runtime import KnowledgeRuntime
from ..dashboard.knowledge_dashboard import ExecutionCard


class DashboardRuntimeBridge:
    """Bridge dashboard — 5 kartu untuk knowledge runtime."""

    def __init__(self, runtime: KnowledgeRuntime) -> None:
        self._runtime = runtime

    def cards(self):
        n = self._runtime.registry.count()
        return [
            ExecutionCard("runtime.engine", "runtime", "ready",
                          "knowledge runtime engine", "preview-only", "ready"),
            ExecutionCard("runtime.pipeline", "runtime", "ready",
                          "Descriptor->Fact->Relation->Knowledge->Preview",
                          "pipeline", "ready"),
            ExecutionCard("runtime.registry", "runtime", "ready",
                          f"{n} knowledge(s) in registry", "knowledge runtime", "ready"),
            ExecutionCard("runtime.no_infer", "runtime", "ready",
                          "no inference, no reasoning", "engine", "ready"),
            ExecutionCard("runtime.deterministic", "runtime", "ready",
                          "synchronous & deterministic", "engine", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
