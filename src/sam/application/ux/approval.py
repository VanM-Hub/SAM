"""Approval UX — approval sebagai execution gate NYATA (M9-003).

Misi menolak keras "Approve -> simulation". Karena itu approval di lapisan
aplikasi ini:
  - Menahan eksekusi sampai user memutuskan (tidak ada auto-approve).
  - user APPROVE  -> status APPROVED, kunci keputusan (immutable), eksekusi
                     diizinkan HANYA oleh ApprovalGate canonical (execution_runtime).
  - user REJECT   -> status REJECTED, eksekusi TIDAK pernah berjalan.
  - Tanpa keputusan user -> WAITING_APPROVAL, eksekusi tidak mungkin.

Boundary approval di sini hanya ORCHESTRATOR keputusan user; evaluasi "apakah
execution boleh jalan" tetap milik ApprovalGate (boundary domain) — service
ini tidak meniru authority-nya, hanya mengirimkan intent user ke gate tsb.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from sam.execution_runtime.approval_gate import ApprovalDecision, ApprovalGate
from sam.execution_runtime.execution_request import ExecutionRequest


class ApprovalStatus(str, Enum):
    PENDING = "pending"              # menunggu keputusan user
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalDecisionIntent(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


@dataclass(frozen=True)
class ApprovalOutcome:
    """Hasil keputusan user setelah melalui ApprovalGate canonical."""

    decision: ApprovalDecision
    status: ApprovalStatus

    def as_dict(self) -> dict:
        return {
            "status": self.status.value,
            "approval_id": self.decision.approval_id,
            "approved": self.decision.approved,
            "reason": self.decision.reason,
            "approver": self.decision.approver,
        }


@dataclass
class ApprovalRequest:
    """Satu permintaan approval yang menunggu keputusan user (mutable status)."""

    approval_id: str
    plan_id: str
    request_id: str
    action_summary: str              # bahasa manusia: "SAM akan membuat issue..."
    gates: List[str] = field(default_factory=list)  # deskripsi langkah yg butuh approval
    status: ApprovalStatus = ApprovalStatus.WAITING_APPROVAL
    decision: Optional[ApprovalDecision] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> dict:
        return {
            "approval_id": self.approval_id,
            "plan_id": self.plan_id,
            "request_id": self.request_id,
            "action_summary": self.action_summary,
            "gates": list(self.gates),
            "status": self.status.value,
            "decision": self.decision.as_dict() if self.decision else None,
            "created_at": self.created_at,
        }


class ApprovalCoordinator:
    """Mengoordinasikan keputusan user ke ApprovalGate canonical (bukan gate sendiri)."""

    def __init__(self, gate: Optional[ApprovalGate] = None) -> None:
        # injeksi gate canonical — evaluasi tetap milik ApprovalGate.
        self._gate = gate or ApprovalGate()
        self._request: Optional[ApprovalRequest] = None

    def record_pending(self, approval: ApprovalRequest) -> None:
        """Daftarkan approval yang menunggu (WAITING_APPROVAL)."""
        approval.status = ApprovalStatus.WAITING_APPROVAL
        self._request = approval

    def pending(self) -> Optional[ApprovalRequest]:
        return self._request

    def decide(
        self, intent: ApprovalDecisionIntent, approver: str = "user"
    ) -> ApprovalOutcome:
        """Terapkan keputusan user lewat ApprovalGate canonical.

        reject  -> REJECTED, eksekusi dilarang (approved=False).
        approve -> dikunci APPROVED; eksekusi boleh jalan HANYA karena
                   ApprovalGate.evaluate mengembalikan approved=True.
        """
        if self._request is None:
            raise RuntimeError("tidak ada pending approval untuk diputuskan")

        req = self._request
        # Build ExecutionRequest untuk gate canonical (mode=execute).
        # provider_id/operation tidak relevan bagi ApprovalGate (ia hanya
        # membaca approved+mode); diisi konstanta aman agar valid.
        execution_request = ExecutionRequest(
            execution_id=req.request_id,
            provider_id="ux.approval",
            operation="approve",
            mode="execute",
            approved=(intent == ApprovalDecisionIntent.APPROVE),
            approver=approver,
        )
        decision = self._gate.evaluate(execution_request)

        if intent == ApprovalDecisionIntent.REJECT:
            req.status = ApprovalStatus.REJECTED
        elif decision.approved:
            req.status = ApprovalStatus.APPROVED
        else:
            # Gate menolak walau user approve -> tetap REJECTED.
            req.status = ApprovalStatus.REJECTED
        req.decision = decision
        return ApprovalOutcome(decision=decision, status=req.status)
