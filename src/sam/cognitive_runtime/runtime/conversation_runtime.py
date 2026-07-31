"""Conversation Runtime Bridge — 5 query read-only (Sprint 191)."""
from __future__ import annotations

from ..foundation.cognitive_registry import CognitiveRegistry
from .cognitive_runtime import CognitiveRuntime
from .cognitive_pipeline import CognitivePipeline
from .cognitive_summary import CognitiveSummarizer
from .cognitive_statistics import CognitiveStatisticsCollector
from .cognitive_engine import CognitiveEngine


class ConversationRuntimeBridge:
    """Bridge conversation — 5 query read-only runtime kognitif."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry
        self._runtime = CognitiveRuntime(registry)
        self._pipeline = CognitivePipeline(registry)
        self._stats = CognitiveStatisticsCollector(registry)

    def query_1_run(self, cognitive_id: str) -> dict:
        r = self._runtime.run(cognitive_id)
        return {"ok": r.ok, "external_calls": r.external_calls, "inferred": r.inferred}

    def query_2_pipeline(self, cognitive_id: str) -> dict:
        p = self._pipeline.run(cognitive_id)
        return {"ok": p.ok, "external_calls": p.external_calls}

    def query_3_stages(self) -> list:
        return self._pipeline.stages()

    def query_4_statistics(self) -> dict:
        s = self._stats.collect()
        return {"total": s.total, "registered": s.registered}

    def query_5_engine(self) -> dict:
        return {
            "no_inference": CognitiveEngine().info().no_inference,
            "is_llm": CognitiveEngine().info().is_llm,
        }
