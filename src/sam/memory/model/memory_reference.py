"""Memory Reference — referensi memori (immutable DTO, Sprint 173).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryReference:
    """Referensi memori (immutable)."""
    reference_id: str
    source_id: str = ""
    target_id: str = ""
    ref_type: str = "points_to"

    def is_valid(self) -> bool:
        return bool(self.reference_id)
