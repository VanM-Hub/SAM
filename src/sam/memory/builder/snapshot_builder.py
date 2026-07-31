"""Snapshot Builder — membangun snapshot memori (Sprint 174).

Phase XVII — Memory Runtime.
Builder hanya membangun DTO. Tidak menyimpan, tidak execute.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class MemorySnapshotDTO:
    """Snapshot memori (immutable, build-only)."""
    snapshot_id: str
    memory_id: str = ""
    state: Dict[str, Any] = field(default_factory=dict)
    external_calls: int = 0


class SnapshotBuilder:
    """Builder snapshot memori. Deterministik."""

    def build(
        self, snapshot_id: str, memory_id: str = "",
        state: Dict[str, Any] = None,
    ) -> MemorySnapshotDTO:
        return MemorySnapshotDTO(
            snapshot_id=snapshot_id, memory_id=memory_id,
            state=dict(state or {}), external_calls=0,
        )
