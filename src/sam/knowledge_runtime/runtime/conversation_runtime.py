"""Conversation Runtime Bridge — query read-only (Sprint 183)."""
from __future__ import annotations

from .knowledge_runtime import KnowledgeRuntime
from .knowledge_summary import KnowledgeSummarizer


class ConversationRuntimeBridge:
    """Bridge conversation — ringkasan knowledge runtime read-only."""

    def __init__(self, runtime: KnowledgeRuntime) -> None:
        self._runtime = runtime

    def summary(self) -> dict:
        s = KnowledgeSummarizer(self._runtime.registry).summary()
        return {"total": s.total_knowledge, "external_calls": s.external_calls}

    def run_status(self, knowledge_id: str) -> dict:
        res = self._runtime.run(knowledge_id)
        return {"ok": res.ok, "steps": res.steps, "external_calls": res.external_calls}
