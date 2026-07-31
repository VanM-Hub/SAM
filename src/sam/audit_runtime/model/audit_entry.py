"""Audit Entry — entri audit immutable (Sprint 213)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class AuditEntry:
    """Entri audit immutable."""
    entry_id: str
    kind: str = "info"
    message: str = ""
    actor: str = ""
    timestamp: int = 0

    def __post_init__(self) -> None:
        if not self.entry_id.strip():
            raise ValueError("entry_id cannot be empty")
