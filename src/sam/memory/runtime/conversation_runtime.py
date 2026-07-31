"""Conversation Runtime Bridge — query read-only (Sprint 175)."""
from __future__ import annotations

from .memory_runtime import MemoryRuntime
from .memory_summary import MemorySummarizer


class ConversationRuntimeBridge:
    """Bridge conversation — ringkasan memori runtime read-only."""

    def __init__(self, runtime: MemoryRuntime) -> None:
        self._runtime = runtime

    def summary(self) -> dict:
        s = MemorySummarizer(self._runtime.registry).summary()
        return {"total": s.total_memories, "external_calls": s.external_calls}

    def run_status(self, memory_id: str) -> dict:
        res = self._runtime.run(memory_id)
        return {"ok": res.ok, "steps": res.steps, "external_calls": res.external_calls}
