"""SQLite Query History — riwayat preview query (read-only).

Sprint 147 — SQLite Provider.
Mencatat riwayat preview query. Tidak ada eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SQLiteHistoryEntry:
    """Satu entri riwayat preview query (immutable)."""
    query_id: str
    query_text: str
    validated: bool = True
    executed: bool = False
    external_calls: int = 0


class SQLiteHistory:
    """Riwayat preview query. Append + read-only query."""

    def __init__(self) -> None:
        self._entries: List[SQLiteHistoryEntry] = []

    def record(self, entry: SQLiteHistoryEntry) -> None:
        self._entries.append(entry)

    def entries(self) -> List[SQLiteHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def total_external_calls(self) -> int:
        return sum(e.external_calls for e in self._entries)


__all__ = ["SQLiteHistory", "SQLiteHistoryEntry"]
