"""Conversation Runtime Bridge — 5 query read-only (Sprint 199)."""
from __future__ import annotations

from ..foundation.workflow_registry import WorkflowRegistry
from .workflow_runtime import WorkflowRuntime
from .workflow_pipeline import WorkflowPipeline
from .workflow_statistics import WorkflowStatisticsCollector
from .workflow_engine import WorkflowEngine


class ConversationRuntimeBridge:
    """Bridge conversation — 5 query read-only runtime workflow."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry
        self._runtime = WorkflowRuntime(registry)
        self._pipeline = WorkflowPipeline(registry)
        self._stats = WorkflowStatisticsCollector(registry)

    def query_1_run(self, workflow_id: str) -> dict:
        r = self._runtime.run(workflow_id)
        return {"ok": r.ok, "external_calls": r.external_calls, "scheduled": r.scheduled}

    def query_2_pipeline(self, workflow_id: str) -> dict:
        p = self._pipeline.run(workflow_id)
        return {"ok": p.ok, "external_calls": p.external_calls}

    def query_3_stages(self) -> list:
        return self._pipeline.stages()

    def query_4_statistics(self) -> dict:
        s = self._stats.collect()
        return {"total": s.total, "registered": s.registered}

    def query_5_engine(self) -> dict:
        return {
            "no_inference": WorkflowEngine().info().no_inference,
            "is_llm": WorkflowEngine().info().is_llm,
        }
