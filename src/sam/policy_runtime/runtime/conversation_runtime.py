"""Conversation Runtime Bridge — 5 query read-only (Sprint 207)."""
from __future__ import annotations

from ..foundation.policy_registry import PolicyRegistry
from .policy_runtime import PolicyRuntime
from .policy_pipeline import PolicyPipeline
from .policy_statistics import PolicyStatisticsCollector
from .policy_engine import PolicyEngine


class ConversationRuntimeBridge:
    """Bridge conversation — 5 query read-only runtime policy."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry
        self._runtime = PolicyRuntime(registry)
        self._pipeline = PolicyPipeline(registry)
        self._stats = PolicyStatisticsCollector(registry)

    def query_1_run(self, policy_id: str) -> dict:
        r = self._runtime.run(policy_id)
        return {"ok": r.ok, "external_calls": r.external_calls, "decided": r.decided}

    def query_2_pipeline(self, policy_id: str) -> dict:
        p = self._pipeline.run(policy_id)
        return {"ok": p.ok, "external_calls": p.external_calls}

    def query_3_stages(self) -> list:
        return self._pipeline.stages()

    def query_4_statistics(self) -> dict:
        s = self._stats.collect()
        return {"total": s.total, "registered": s.registered}

    def query_5_engine(self) -> dict:
        return {
            "no_inference": PolicyEngine().info().no_inference,
            "is_llm": PolicyEngine().info().is_llm,
        }
