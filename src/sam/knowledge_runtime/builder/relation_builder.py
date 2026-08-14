"""Relation Builder — membangun relasi knowledge (Sprint 182).

Phase XVIII — Knowledge Runtime.
Builder hanya membangun DTO. Tidak inferensi.
"""
from __future__ import annotations
from ..model.knowledge_relation import KnowledgeRelationPreview


class RelationBuilder:
    """Builder relasi knowledge. Deterministik."""

    def build(
        self, relation_id: str, source_id: str = "",
        target_id: str = "", rel_type: str = "relates_to",
    ) -> KnowledgeRelationPreview:
        return KnowledgeRelationPreview(
            relation_id=relation_id, source_id=source_id,
            target_id=target_id, rel_type=rel_type,
        )
