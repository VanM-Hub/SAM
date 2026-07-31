"""Rollback Report (Sprint 255).

Program C - Real Execution Runtime.
Laporan immutable hasil rollback (metadata).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RollbackReport:
    """Laporan rollback (immutable)."""
    report_id: str
    rollback_id: str
    execution_id: str
    status: str = "ok"  # ok | failed | skipped
    restored_metadata: tuple = field(default_factory=tuple)
    external_calls: int = 0
    error: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "rollback_id": self.rollback_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "restored_metadata": list(self.restored_metadata),
            "external_calls": self.external_calls,
            "error": self.error,
        }
