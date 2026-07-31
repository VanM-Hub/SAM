"""Approval Summary (Sprint 252).

Program C - Real Execution Runtime.
Rangkuman immutable status approval untuk laporan/dashboard.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from .approval_gate import ApprovalDecision


@dataclass(frozen=True)
class ApprovalSummary:
    """Ringkasan approval (immutable)."""
    total: int = 0
    approved: int = 0
    rejected: int = 0
    pending: int = 0

    def add(self, decision: ApprovalDecision) -> "ApprovalSummary":
        total = self.total + 1
        approved = self.approved + (1 if decision.approved else 0)
        rejected = self.rejected + (0 if decision.approved else 1)
        return ApprovalSummary(total=total, approved=approved, rejected=rejected, pending=0)

    def to_dict(self) -> dict:
        return {"total": self.total, "approved": self.approved,
                "rejected": self.rejected, "pending": self.pending}
