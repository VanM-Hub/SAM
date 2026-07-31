"""Approval Validator (Sprint 252).

Program C - Real Execution Runtime.
Validasi bahwa approval memenuhi aturan (deterministic, no network).
Approver wajib hanya saat execute yang benar-benar membutuhkan persetujuan;
preview/rollback tidak mewajibkan approver.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple

from .approval_gate import ApprovalDecision


@dataclass(frozen=True)
class ApprovalValidatorResult:
    """Hasil validasi approval (immutable)."""
    approval_id: str
    valid: bool
    errors: tuple = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "approval_id": self.approval_id,
            "valid": self.valid,
            "errors": list(self.errors),
        }


class ApprovalValidator:
    """Validasi struktur keputusan approval. Read-only."""

    def validate(self, decision: ApprovalDecision,
                 *, require_approver: bool = True) -> ApprovalValidatorResult:
        errors = []
        if not decision.approval_id:
            errors.append("approval_id required")
        if not decision.approved and not decision.reason:
            errors.append("reason required when rejected")
        if decision.approved and require_approver and not decision.approver:
            errors.append("approver required when approved")
        return ApprovalValidatorResult(
            approval_id=decision.approval_id,
            valid=len(errors) == 0,
            errors=tuple(errors),
        )
