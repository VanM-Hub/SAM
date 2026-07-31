"""Reference Builder — membangun referensi memori (Sprint 174).

Phase XVII — Memory Runtime.
Builder hanya membangun DTO. Tidak menyimpan, tidak execute.
"""
from __future__ import annotations
from ..model.memory_reference import MemoryReference


class ReferenceBuilder:
    """Builder referensi memori. Deterministik."""

    def build(
        self, reference_id: str, source_id: str = "",
        target_id: str = "", ref_type: str = "points_to",
    ) -> MemoryReference:
        return MemoryReference(
            reference_id=reference_id, source_id=source_id,
            target_id=target_id, ref_type=ref_type,
        )
