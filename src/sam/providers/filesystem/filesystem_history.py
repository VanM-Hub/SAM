"""Filesystem History — riwayat preview filesystem (read-only).

Sprint 145 — Filesystem Provider.
Mencatat ringkasan preview. Tidak ada eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class FilesystemHistoryEntry:
    """Satu entri riwayat preview filesystem (immutable)."""
    request_id: str
    operation: str
    path: str
    ok: bool = True
    external_calls: int = 0


class FilesystemHistory:
    """Riwayat preview filesystem. Append + read-only query."""

    def __init__(self) -> None:
        self._entries: List[FilesystemHistoryEntry] = []

    def record(self, entry: FilesystemHistoryEntry) -> None:
        self._entries.append(entry)

    def entries(self) -> List[FilesystemHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def total_external_calls(self) -> int:
        return sum(e.external_calls for e in self._entries)
