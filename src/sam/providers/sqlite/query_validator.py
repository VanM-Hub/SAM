"""SQLite Query Validator — validasi query (deterministik).

Sprint 147 — SQLite Provider.
Memvalidasi query tanpa koneksi database.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .query_builder import SQLiteQuery

# Operasi SQL yang bersifat destruktif/eksekusi nyata (defensive)
BLOCKED_SQL_KEYWORDS = {"drop ", "delete from", "truncate ", "pragma ", "attach "}


@dataclass(frozen=True)
class SQLiteQueryValidation:
    """Hasil validasi query (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class SQLiteQueryValidator:
    """Validator query SQLite. Deterministik, build-only."""

    def validate(self, query: SQLiteQuery) -> SQLiteQueryValidation:
        issues = []
        if not query.query_id:
            issues.append("query_id required")
        if not query.sql:
            issues.append("sql required")
        lowered = query.sql.lower()
        for keyword in BLOCKED_SQL_KEYWORDS:
            if keyword in lowered:
                issues.append(f"forbidden keyword: {keyword.strip()} (read-only preview)")
        return SQLiteQueryValidation(valid=not issues, issues=issues)
