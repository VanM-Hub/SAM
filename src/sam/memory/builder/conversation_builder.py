"""Conversation Builder Bridge — query read-only (Sprint 174)."""
from __future__ import annotations

from .memory_builder import MemoryBuilder


class ConversationBuilderBridge:
    """Bridge conversation — ringkasan builder memori read-only."""

    def __init__(self, builder: MemoryBuilder = None) -> None:
        self._builder = builder or MemoryBuilder()

    def summary(self, memory_id: str) -> dict:
        res = self._builder.build(memory_id)
        return {"valid": res.valid, "reason": res.reason}

    def describe_builder(self) -> str:
        return "memory builder (build-only, no store, no execute)"
