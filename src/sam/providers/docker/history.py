"""Docker History — riwayat preview docker (read-only).

Sprint 148 — Docker Provider.
Mencatat riwayat preview. Tidak ada eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class DockerHistoryEntry:
    """Satu entri riwayat preview docker (immutable)."""
    request_id: str
    kind: str
    name: str
    operation: str
    executed: bool = False
    external_calls: int = 0


class DockerHistory:
    """Riwayat preview docker. Append + read-only query."""

    def __init__(self) -> None:
        self._entries: List[DockerHistoryEntry] = []

    def record(self, entry: DockerHistoryEntry) -> None:
        self._entries.append(entry)

    def entries(self) -> List[DockerHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def total_external_calls(self) -> int:
        return sum(e.external_calls for e in self._entries)
