"""SQLite Query Preview — preview query tanpa eksekusi.

Sprint 147 — SQLite Provider.
Menghasilkan preview eksekusi query (simulasi). Tidak menjalankan apa pun.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .query_builder import SQLiteQuery


@dataclass(frozen=True)
class SQLitePreview:
    """Preview eksekusi query (immutable)."""
    query_id: str
    query_text: str
    preview: bool = True
    connected: bool = False
    executed: bool = False
    external_calls: int = 0
    notes: List[str] = field(default_factory=list)


class SQLiteQueryPreview:
    """Preview query SQLite — external_calls selalu 0."""

    def preview(self, query: SQLiteQuery) -> SQLitePreview:
        return SQLitePreview(
            query_id=query.query_id,
            query_text=query.render(),
            preview=True,
            connected=False,
            executed=False,
            external_calls=0,
            notes=["dry-run: no database accessed"],
        )
