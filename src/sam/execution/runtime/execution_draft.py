"""Execution Draft — frozen DTO hasil draft eksekusi."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ExecutionDraft:
    """Draft hasil eksekusi runtime."""
    draft_id: str
    context_id: str
    candidates: int
    types_used: List[str]
    summary: str
