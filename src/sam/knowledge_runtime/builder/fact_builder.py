"""Fact Builder — membangun fakta knowledge (Sprint 182).

Phase XVIII — Knowledge Runtime.
Builder hanya membangun DTO. Tidak inferensi.
"""
from __future__ import annotations
from ..model.knowledge_fact import KnowledgeFactPreview


class FactBuilder:
    """Builder fakta knowledge. Deterministik."""

    def build(
        self, fact_id: str, subject: str = "",
        predicate: str = "is", obj: str = "", source: str = None,
    ) -> KnowledgeFactPreview:
        return KnowledgeFactPreview(
            fact_id=fact_id, subject=subject, predicate=predicate,
            obj=obj, source=source,
        )
