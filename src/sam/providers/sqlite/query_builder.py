"""SQLite Query Builder — membangun query SQLite (preview).

Sprint 147 — SQLite Provider.
Menyusun representasi query tanpa eksekusi. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class SQLiteQuery:
    """Representasi query (immutable, tidak pernah dijalankan)."""
    query_id: str
    sql: str
    table: Optional[str] = None
    params: List[str] = field(default_factory=list)
    limit: Optional[int] = None

    def render(self) -> str:
        """Reproduksi query sebagai string (preview, bukan eksekusi)."""
        base = self.sql
        if self.limit is not None:
            base = f"{base} LIMIT {self.limit}"
        return base


class SQLiteQueryBuilder:
    """Builder query SQLite — deterministic, build-only."""

    def build(
        self,
        query_id: str,
        sql: str,
        table: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> SQLiteQuery:
        return SQLiteQuery(
            query_id=query_id,
            sql=sql,
            table=table,
            limit=limit,
        )
