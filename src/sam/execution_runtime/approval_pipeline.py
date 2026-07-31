"""Approval Pipeline (Sprint 252).

Program C - Real Execution Runtime.
Pipeline: Preview -> Approval Runtime -> Execution Ready.
Execution hanya siap bila approved == True.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .approval_gate import ApprovalGate, ApprovalDecision
from .approval_validator import ApprovalValidator, ApprovalValidatorResult
from .execution_request import ExecutionRequest


@dataclass(frozen=True)
class ApprovalPipelineResult:
    """Hasil pipeline approval (immutable)."""
    pipeline_id: str
    execution_id: str
    state: str  # preview | awaiting_approval | execution_ready | blocked
    approved: bool
    decision: ApprovalDecision
    validation: ApprovalValidatorResult
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "execution_id": self.execution_id,
            "state": self.state,
            "approved": self.approved,
            "decision": self.decision.as_dict(),
            "validation": self.validation.as_dict(),
            "external_calls": self.external_calls,
        }


class ApprovalPipeline:
    """Pipeline approval. Read-only gate, no network."""

    def __init__(self, gate: ApprovalGate | None = None, validator: ApprovalValidator | None = None) -> None:
        self._gate = gate or ApprovalGate()
        self._validator = validator or ApprovalValidator()

    def run(self, pipeline_id: str, request: ExecutionRequest) -> ApprovalPipelineResult:
        decision = self._gate.evaluate(request)
        # approver wajib hanya saat mode execute (yang benar-benar butuh approval)
        validation = self._validator.validate(decision, require_approver=(request.mode == "execute"))
        if not validation.valid:
            state = "blocked"
        elif request.mode == "execute":
            state = "execution_ready" if decision.approved else "awaiting_approval"
        else:
            state = "preview"
        return ApprovalPipelineResult(
            pipeline_id=pipeline_id,
            execution_id=request.execution_id,
            state=state,
            approved=decision.approved,
            decision=decision,
            validation=validation,
            external_calls=0,
        )

    def may_execute(self, request: ExecutionRequest) -> bool:
        return self._gate.may_execute(request)
