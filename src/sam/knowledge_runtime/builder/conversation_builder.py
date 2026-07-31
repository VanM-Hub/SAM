"""Conversation Builder Bridge — query read-only (Sprint 182)."""
from __future__ import annotations

from .knowledge_builder import KnowledgeBuilder


class ConversationBuilderBridge:
    """Bridge conversation — ringkasan builder knowledge read-only."""

    def __init__(self, builder: KnowledgeBuilder = None) -> None:
        self._builder = builder or KnowledgeBuilder()

    def summary(self, knowledge_id: str) -> dict:
        res = self._builder.build(knowledge_id)
        return {"valid": res.valid, "reason": res.reason}

    def describe_builder(self) -> str:
        return "knowledge builder (build-only, no inference, no store)"
