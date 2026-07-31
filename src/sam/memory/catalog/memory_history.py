"""Memory History — riwayat memori (Sprint 176).

Phase XVII — Memory Runtime.
Read-only query.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MemoryHistoryEntry:
    """Satu entri riwayat memori (immutable)."""
    memory_id: str
    action: str
    version: str = "1.0.0"
    external_calls: int = 0


class MemoryHistory:
    """Riwayat memori. Append + read-only query."""

    def __init__(self) -> None:
        self._entries: List[MemoryHistoryEntry] = []

    def record(self, entry: MemoryHistoryEntry) -> None:
        self._entries.append(entry)

    def entries(self, memory_id: str = None) -> List[MemoryHistoryEntry]:
        if memory_id is None:
            return list(self._entries)
        return [e for e in self._entries if e.memory_id == memory_id]

    def count(self) -> int:
        return len(self._entries)
