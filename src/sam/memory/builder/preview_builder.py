"""Preview Builder — membangun preview memori (Sprint 174).

Phase XVII — Memory Runtime.
Preview-only, external_calls selalu 0. Tidak menyimpan, tidak execute.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MemoryPreviewDTO:
    """Preview memori (immutable)."""
    preview_id: str
    memory_id: str = ""
    preview: bool = True
    stored: bool = False
    external_calls: int = 0
    notes: List[str] = field(default_factory=list)


class PreviewBuilder:
    """Builder preview memori. external_calls selalu 0."""

    def build(self, preview_id: str, memory_id: str = "") -> MemoryPreviewDTO:
        return MemoryPreviewDTO(
            preview_id=preview_id, memory_id=memory_id,
            preview=True, stored=False, external_calls=0,
            notes=["dry-run: no data stored"],
        )
