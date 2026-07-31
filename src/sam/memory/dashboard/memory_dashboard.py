"""Dashboard Memory — ExecutionCard base (Phase XVII, Sprint 172+).

Semua dashboard bridge memory menghasilkan 5 immutable ExecutionCard.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionCard:
    """Kartu eksekusi immutable untuk dashboard memory (read-only)."""
    card_id: str
    category: str = "memory"
    state: str = "unknown"
    summary: str = ""
    detail: str = ""
    verdict: str = "pending"


__all__ = ["ExecutionCard"]
