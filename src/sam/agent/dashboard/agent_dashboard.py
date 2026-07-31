"""Dashboard Agent — ExecutionCard base (Phase XV).

Sprint 156+ — dashboard bridge read-only.
Semua dashboard bridge agent menghasilkan 5 immutable ExecutionCard.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ExecutionCard:
    """Kartu eksekusi immutable untuk dashboard agent (read-only)."""
    card_id: str
    category: str = "agent"
    state: str = "unknown"
    summary: str = ""
    detail: str = ""
    verdict: str = "pending"


__all__ = ["ExecutionCard"]
