"""Dashboard Skill — ExecutionCard base (Phase XVI, Sprint 164+).

Semua dashboard bridge skill menghasilkan 5 immutable ExecutionCard.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionCard:
    """Kartu eksekusi immutable untuk dashboard skill (read-only)."""
    card_id: str
    category: str = "skill"
    state: str = "unknown"
    summary: str = ""
    detail: str = ""
    verdict: str = "pending"


__all__ = ["ExecutionCard"]
