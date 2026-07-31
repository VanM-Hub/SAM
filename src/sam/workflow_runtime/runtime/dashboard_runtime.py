"""Dashboard Runtime Bridge — 5 WorkflowCards (Sprint 199)."""
from __future__ import annotations

from ..dashboard import WorkflowCard
from ..foundation.workflow_registry import WorkflowRegistry
from .workflow_runtime import WorkflowRuntime
from .workflow_pipeline import WorkflowPipeline
from .workflow_engine import WorkflowEngine


class DashboardRuntimeBridge:
    """Bridge dashboard — 5 kartu untuk runtime workflow."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry
        self._runtime = WorkflowRuntime(registry)
        self._pipeline = WorkflowPipeline(registry)

    def cards(self):
        n = self._registry.count()
        verdict = "ready" if n > 0 else "empty"
        return [
            WorkflowCard("rt.workflow", "runtime", verdict,
                         f"{n} workflow(s) runnable", "workflow runtime", verdict),
            WorkflowCard("rt.pipeline", "runtime", "ready",
                         "Descriptor->Workflow->Builder->Preview",
                         "pipeline", "ready"),
            WorkflowCard("rt.preview", "runtime", "ready",
                         "no scheduling, external_calls=0", "preview", "ready"),
            WorkflowCard("rt.engine", "runtime", "ready",
                         "engine: not LLM, not AI, deterministic", "engine", "ready"),
            WorkflowCard("rt.summary", "runtime", "ready",
                         "WorkflowSummarizer deterministic", "summary", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
