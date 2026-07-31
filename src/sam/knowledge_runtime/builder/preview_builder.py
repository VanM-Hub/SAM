"""Preview Builder — membangun preview knowledge (Sprint 182).

Phase XVIII — Knowledge Runtime.
Preview-only, external_calls selalu 0. Tidak menyimpan.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class KnowledgePreviewDTO:
    """Preview knowledge (immutable)."""
    preview_id: str
    knowledge_id: str = ""
    preview: bool = True
    stored: bool = False
    inferred: bool = False
    external_calls: int = 0
    notes: List[str] = field(default_factory=list)


class PreviewBuilder:
    """Builder preview knowledge. No store, no infer, external_calls=0."""

    def build(self, preview_id: str, knowledge_id: str = "") -> KnowledgePreviewDTO:
        return KnowledgePreviewDTO(
            preview_id=preview_id, knowledge_id=knowledge_id,
            preview=True, stored=False, inferred=False, external_calls=0,
            notes=["dry-run: no data stored, no inference"],
        )
