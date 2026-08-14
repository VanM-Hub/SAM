"""M14-002 DelegatedApprovalProvider — jembatan authority -> ApprovalGate.

Fungsi: menentukan apakah "delegated authority mengizinkan approval diberikan
secara otomatis" untuk sebuah ExecutionRequest, TANPA menurunkan semantik
approval.

Sesuai ARSITEKTURAL RULE M14:
    Approval tetap satu.
    Execution tetap canonical.
    Autonomous hanya menentukan: apakah delegated authority mengizinkan
    Approval diberikan otomatis untuk tindakan ini?

Provider ini TIDAK mengeksekusi connector, TIDAK membuat executor kedua,
dan TIDAK pernah mengubah credential. Ia hanya MENGHASILKAN status approval
yang sah (approved True/False + approver="delegated") yang kemudian tetap
diperiksa ulang oleh ApprovalGate canonical sebelum eksekusi.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sam.delegated_authority.authority import (
    AuthorityVerdict,
)
from sam.delegated_authority.evaluation import AuthorityEvaluation
from sam.execution_runtime.approval_gate import ApprovalGate
from sam.execution_runtime.execution_request import ExecutionRequest


class ApprovalSource(str):
    USER = "user"
    DELEGATED = "delegated"


@dataclass(frozen=True)
class DelegatedApprovalOutcome:
    """Hasil keputusan approval dari jalur delegated (immutable)."""

    approval_id: str
    execution_id: str
    approved: bool
    source: str                       # user | delegated
    verdict: str = ""                 # auto_approve | escalate | blocked | no_authority
    reason: str = ""
    approver: str = ""
    authority: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "execution_id": self.execution_id,
            "approved": self.approved,
            "source": self.source,
            "verdict": self.verdict,
            "reason": self.reason,
            "approver": self.approver,
            "authority": self.authority,
        }


class DelegatedApprovalProvider:
    """Menilai delegated authority lalu menembus ApprovalGate canonical.

    Alur:
        AuthorityEvaluation -> AutonomousAuthority (verdict)
        -> bila AUTO_APPROVE: build ExecutionRequest.approved=True, approver
           = "delegated:<ward_id>", lalu VERIFIKASI ulang via ApprovalGate.
        -> selain itu: approved=False (tidak pernah auto-execute), verdict
           escalate/blocked/no_authority -> pemanggil harus eskalasi/rollback.

    ApprovalGate TETAP sumber keputusan eksekusi; provider ini hanya menyiapkan
    input approval yang sah dari delegated authority. Tidak pernah mengeksekusi.
    """

    def __init__(
        self,
        evaluation: Optional[AuthorityEvaluation] = None,
        gate: Optional[ApprovalGate] = None,
    ) -> None:
        self._evaluation = evaluation or AuthorityEvaluation()
        self._gate = gate or ApprovalGate()
        self._outcomes: Dict[str, DelegatedApprovalOutcome] = {}

    # --- public API ---

    async def approve_for(
        self,
        request: ExecutionRequest,
        *,
        grant,
        risk: float = 0.0,
        risk_label: str = "low",
        evidence_refs: tuple = (),
        action_context: Optional[Dict[str, Any]] = None,
    ) -> DelegatedApprovalOutcome:
        """Evaluasi + siapkan approval utk satu execution request (mutation).

        `grant` = DelegationGrant (proyeksi Entrustment owner) atau None.
        Mengembalikan status approval SAH. Jika approved=True, caller
        meneruskan request ke canonical executor yang WAJIB memakai
        ApprovalGate (defense in depth). Provider ini sendiri TIDAK eksekusi.
        """
        # Ambil ward_id dari konteks / request (payload memuat subject).
        ward_id = str(action_context.get("ward_id", "") if action_context else "") \
                  or request.payload.get("ward_id", "")
        capability = request.operation

        authority = await self._evaluation.evaluate(
            ward_id=ward_id,
            capability=capability,
            grant=grant,
            risk=risk,
            risk_label=risk_label,
            evidence_refs=evidence_refs,
            action_context=action_context,
        )

        approved = authority.verdict == AuthorityVerdict.AUTO_APPROVE
        approver = f"delegated:{authority.ward_id}" if approved else ""

        # Bangun request bersih utk ApprovalGate (approved sesuai verdict).
        gate_request = ExecutionRequest(
            execution_id=request.execution_id,
            provider_id=request.provider_id,
            operation=request.operation,
            payload=request.payload,
            mode="execute",
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries,
            approved=approved,
            approver=approver,
            deterministic=request.deterministic,
            synchronous=request.synchronous,
        )
        # ApprovalGate tetap penentu final (defense in depth).
        gate_decision = self._gate.evaluate(gate_request)

        outcome = DelegatedApprovalOutcome(
            approval_id=gate_decision.approval_id,
            execution_id=request.execution_id,
            approved=approved and gate_decision.approved,
            source=ApprovalSource.DELEGATED if approved else ApprovalSource.USER,
            verdict=authority.verdict.value,
            reason=authority.reason,
            approver=approver,
            authority=authority.as_dict(),
        )
        self._outcomes[request.execution_id] = outcome
        return outcome

    def may_execute(self, request: ExecutionRequest) -> bool:
        """True bila request ini sudah punya approval delegated yang sah."""
        return self._gate.may_execute(request)

    def outcome(self, execution_id: str) -> Optional[DelegatedApprovalOutcome]:
        return self._outcomes.get(execution_id)

    def full_request(
        self, request: ExecutionRequest, outcome: DelegatedApprovalOutcome
    ) -> ExecutionRequest:
        """Kembalikan ExecutionRequest yang sudah berapproved sesuai outcome."""
        return ExecutionRequest(
            execution_id=request.execution_id,
            provider_id=request.provider_id,
            operation=request.operation,
            payload=request.payload,
            mode="execute",
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries,
            approved=outcome.approved,
            approver=outcome.approver,
            deterministic=request.deterministic,
            synchronous=request.synchronous,
        )
