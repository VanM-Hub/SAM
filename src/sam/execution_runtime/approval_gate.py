"""Approval Gate (Sprint 252).

Program C - Real Execution Runtime.
Gate yang mengharuskan approval sebelum execute. Tanpa approved==True,
eksekusi tidak pernah boleh berjalan (external_calls tetap 0).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from .execution_request import ExecutionRequest


@dataclass(frozen=True)
class ApprovalDecision:
    """Keputusan approval (immutable)."""
    approval_id: str
    execution_id: str
    approved: bool
    reason: str = ""
    approver: str = ""

    def as_dict(self) -> dict:
        return {
            "approval_id": self.approval_id,
            "execution_id": self.execution_id,
            "approved": self.approved,
            "reason": self.reason,
            "approver": self.approver,
        }


class ApprovalGate:
    """Gate approval. Menolak eksekusi bila approved == False."""

    def evaluate(self, request: ExecutionRequest) -> ApprovalDecision:
        can_execute = request.approved
        if request.mode != "execute":
            can_execute = True  # preview/rollback tidak butuh approval
        return ApprovalDecision(
            approval_id=f"ap-{request.execution_id}",
            execution_id=request.execution_id,
            approved=can_execute,
            reason="" if can_execute else "approval required before execute",
            approver=request.approver if can_execute else "",
        )

    def may_execute(self, request: ExecutionRequest) -> bool:
        return self.evaluate(request).approved
