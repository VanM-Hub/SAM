"""Dashboard Knowledge — ExecutionCard base (Phase XVIII, Sprint 180+).

Semua dashboard bridge knowledge menghasilkan 5 immutable ExecutionCard.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionCard:
    """Kartu eksekusi immutable untuk dashboard knowledge (read-only)."""
    card_id: str
    category: str = "knowledge"
    state: str = "unknown"
    summary: str = ""
    detail: str = ""
    verdict: str = "pending"


__all__ = ["ExecutionCard"]
