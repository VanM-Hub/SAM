"""Audit Record — model record audit immutable (Sprint 213).

Immutable audit record: tidak bisa diubah setelah dibuat (frozen + non-mutable).
Read-only, tanpa penyimpanan maupun eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class AuditRecord:
    """Record audit immutable — sumber provenance deterministik."""
    record_id: str
    action: str = "observe"
    source: str = ""
    target: str = ""
    trace_id: str = ""
    entries: List["AuditEntry"] = field(default_factory=list)
    immutable: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))
        if not self.record_id.strip():
            raise ValueError("record_id cannot be empty")
