"""Knowledge Builder — membangun DTO knowledge (Sprint 182).

Phase XVIII — Knowledge Runtime.
Builder hanya membangun DTO. Tidak inferensi, tidak reasoning, tidak menyimpan.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ..foundation.knowledge_descriptor import KnowledgeDescriptor
from ..model.knowledge_record import KnowledgeRecord


@dataclass(frozen=True)
class KnowledgeBuildResult:
    """Hasil pembangunan knowledge (immutable)."""
    descriptor: Optional[KnowledgeDescriptor] = None
    record: Optional[KnowledgeRecord] = None
    valid: bool = False
    reason: str = ""


class KnowledgeBuilder:
    """Builder knowledge. Deterministik, build-only."""

    def build(
        self,
        knowledge_id: str,
        name: str = "",
        category: str = "general",
        version: str = "1.0.0",
    ) -> KnowledgeBuildResult:
        if not knowledge_id:
            return KnowledgeBuildResult(valid=False, reason="knowledge_id required")
        descriptor = KnowledgeDescriptor(
            id=knowledge_id, name=name or knowledge_id, version=version,
            category=category,
        )
        record = KnowledgeRecord(
            record_id=f"rec.{knowledge_id}", knowledge_id=knowledge_id,
        )
        return KnowledgeBuildResult(
            descriptor=descriptor, record=record, valid=True,
        )
