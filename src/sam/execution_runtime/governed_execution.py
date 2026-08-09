"""Governed Execution - IP-4.1-002 WP-11/12/15/17.

Governed Execution.
Menghubungkan Execution dengan Governance menjadi satu jalur end-to-end:
Approval Binding -> Execution Authorization -> Execution -> Verification ->
Evidence -> Execution API.

Scope (Foundation immutable):
- Execution hanya dapat berjalan setelah Approval (Article V).
- Seluruh execution menghasilkan evidence (Article II/XI).
- Seluruh execution dapat dijelaskan (Article XIV).
- Execution authorization eksplisit & deterministik (Article VII).

Tidak menambah authority; menjalankan guard yang sudah ada (Approval Gate)
sebagai satu komposisi read-only + state terbatas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .execution_request import ExecutionRequest
from .execution_response import ExecutionResponse
from .execution_runtime import ExecutionRuntime, ExecutionOutcome
from .approval_gate import ApprovalGate, ApprovalDecision
from .execution_verification import ExecutionVerifier, ExecutionVerification
from .execution_explainer import ExecutionExplainer, ExecutionExplanation
from .execution_audit import ExecutionAudit, AuditTimelineStep, ExecutionAuditRecord


@dataclass(frozen=True)
class ExecutionEvidence:
    """Evidence hasil execution yang di-govern (immutable, Article II)."""

    execution_id: str
    provider_id: str
    operation: str
    status: str
    external_calls: int
    executed: bool
    verification: Optional[str]          # verification_id, bila ada
    explanation_id: str = ""
    audit_id: str = ""

    def as_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "status": self.status,
            "external_calls": self.external_calls,
            "executed": self.executed,
            "verification": self.verification,
            "explanation_id": self.explanation_id,
            "audit_id": self.audit_id,
        }


@dataclass(frozen=True)
class GovernedExecutionResult:
    """Hasil akhir execution yang di-govern (immutable)."""

    execution_id: str
    approval: ApprovalDecision
    outcome: Optional[ExecutionOutcome]
    verification: ExecutionVerification
    explanation: ExecutionExplanation
    evidence: ExecutionEvidence
    audit: Optional[ExecutionAuditRecord]
    executed: bool

    def as_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "approval": self.approval.as_dict(),
            "outcome": self.outcome.as_dict() if self.outcome else None,
            "verification": self.verification.as_dict(),
            "explanation": self.explanation.as_dict(),
            "evidence": self.evidence.as_dict(),
            "audit": self.audit.as_dict() if self.audit else None,
            "executed": self.executed,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GovernedExecution:
    """Jalur eksekusi governed end-to-end (read-only + audit collection).

    Komposisi approval -> runtime -> verifikasi -> explain -> evidence -> audit.
    Tidak mengubah Approval Gate; hanya memakainya dengan disiplin.
    """

    def __init__(
        self,
        runtime: Optional[ExecutionRuntime] = None,
        gate: Optional[ApprovalGate] = None,
        verifier: Optional[ExecutionVerifier] = None,
        explainer: Optional[ExecutionExplainer] = None,
        audit: Optional[ExecutionAudit] = None,
    ) -> None:
        self._runtime = runtime or ExecutionRuntime()
        self._gate = gate or ApprovalGate()
        self._verifier = verifier or ExecutionVerifier()
        self._explainer = explainer or ExecutionExplainer()
        self._audit = audit or ExecutionAudit()

    @property
    def audit(self) -> ExecutionAudit:
        return self._audit

    def execute(self, request: ExecutionRequest, policy_id: str = "") -> GovernedExecutionResult:
        """Eksekusi governed. Menghasilkan outcome + verification + evidence + audit.

        Mengembalikan hasil; TIDAK men-trigger eksekusi nyata di luar jalur
        yang sudah approval-gated oleh pipeline/runtime.
        """
        # 1. Approval binding & authorization
        decision = self._gate.evaluate(request)

        # 2. Eksekusi lewat runtime (pipeline approval-gated)
        outcome = None
        executed = False
        if decision.approved and request.mode == "execute":
            outcome = self._runtime.run("gov-{}".format(request.execution_id), request)
            executed = bool(outcome and outcome.executed)

        # 3. Response (dari outcome atau fallback)
        response: ExecutionResponse
        if outcome is not None and outcome.result is not None:
            response = outcome.result.response
        else:
            response = ExecutionResponse(
                execution_id=request.execution_id,
                provider_id=request.provider_id,
                operation=request.operation,
                status="blocked" if request.mode == "execute" else "preview",
                mode=request.mode,
                external_calls=0,
            )

        # 4. Verifikasi
        verification = self._verifier.verify(request, response)

        # 5. Explainer
        explanation = self._explainer.explain(
            request, response, approved=decision.approved, policy_id=policy_id)

        # 6. Evidence
        calls = getattr(response, "external_calls", 0)
        evidence = ExecutionEvidence(
            execution_id=request.execution_id,
            provider_id=request.provider_id,
            operation=request.operation,
            status=getattr(response, "status", "unknown"),
            external_calls=calls,
            executed=executed,
            verification=verification.verification_id,
            explanation_id=explanation.explanation_id,
            audit_id="aud-{}-0".format(request.execution_id),
        )

        # 7. Audit (timeline lengkap)
        timeline = (
            AuditTimelineStep("approval", "ok" if decision.approved else "blocked",
                              detail=decision.reason),
            AuditTimelineStep("execution", "executed" if executed else getattr(response, "status", "unknown"),
                              external_calls=calls),
            AuditTimelineStep("verification", "ok" if verification.passed else "failed"),
        )
        audit_rec = self._audit.record(
            execution_id=request.execution_id,
            provider_id=request.provider_id,
            operation=request.operation,
            mode=request.mode,
            status=getattr(response, "status", "unknown"),
            timeline=timeline,
            approver=request.approver or "",
            approval_id=decision.approval_id,
        )

        return GovernedExecutionResult(
            execution_id=request.execution_id,
            approval=decision,
            outcome=outcome,
            verification=verification,
            explanation=explanation,
            evidence=evidence,
            audit=audit_rec,
            executed=executed,
        )
