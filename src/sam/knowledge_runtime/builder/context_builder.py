"""Context Builder — membangun konteks knowledge (Sprint 182).

Phase XVIII — Knowledge Runtime.
Builder hanya membangun DTO. Tidak reasoning.
"""
from __future__ import annotations
from ..model.knowledge_context import KnowledgeContext


class ContextBuilder:
    """Builder konteks knowledge. Deterministik."""

    def build(
        self, context_id: str, knowledge_id: str = "",
        values: dict = None,
    ) -> KnowledgeContext:
        return KnowledgeContext(
            context_id=context_id, knowledge_id=knowledge_id,
            values=dict(values or {}),
        )
