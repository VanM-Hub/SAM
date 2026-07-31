"""Memory Builder — membangun DTO memori (Sprint 174).

Phase XVII — Memory Runtime.
Builder hanya membangun DTO. Tidak menyimpan, tidak execute.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ..foundation.memory_descriptor import MemoryDescriptor
from ..model.memory_record import MemoryRecord


@dataclass(frozen=True)
class MemoryBuildResult:
    """Hasil pembangunan memori (immutable)."""
    descriptor: Optional[MemoryDescriptor] = None
    record: Optional[MemoryRecord] = None
    valid: bool = False
    reason: str = ""


class MemoryBuilder:
    """Builder memori. Deterministik, build-only."""

    def build(
        self,
        memory_id: str,
        name: str = "",
        category: str = "general",
        version: str = "1.0.0",
    ) -> MemoryBuildResult:
        if not memory_id:
            return MemoryBuildResult(valid=False, reason="memory_id required")
        descriptor = MemoryDescriptor(
            id=memory_id, name=name or memory_id, version=version, category=category,
        )
        record = MemoryRecord(record_id=f"rec.{memory_id}", memory_id=memory_id)
        return MemoryBuildResult(
            descriptor=descriptor, record=record, valid=True,
        )
