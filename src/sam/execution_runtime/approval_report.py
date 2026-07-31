"""Approval Report (Sprint 252).

Program C - Real Execution Runtime.
Laporan immutable riwayat approval.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .approval_gate import ApprovalDecision


@dataclass(frozen=True)
class ApprovalReport:
    """Laporan approval (immutable)."""
    report_id: str
    decisions: tuple = field(default_factory=tuple)
    generated_at: str = ""

    def all_approved(self) -> bool:
        return all(d.approved for d in self.decisions)

    def as_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "decisions": [d.as_dict() for d in self.decisions],
            "generated_at": self.generated_at,
        }
