"""Knowledge Relation — relasi knowledge (immutable DTO, Sprint 181).

Phase XVIII — Knowledge Runtime.
Relation menghubungkan dua entitas. Tidak inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeRelationPreview:
    """Relasi knowledge (immutable, preview/read-only DTO)."""
    relation_id: str
    source_id: str = ""
    target_id: str = ""
    rel_type: str = "relates_to"

    def is_valid(self) -> bool:
        return bool(self.relation_id) and bool(self.source_id)
