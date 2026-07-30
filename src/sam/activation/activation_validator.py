"""Activation Validator — validasi draft aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_draft import ActivationDraft
from sam.activation.activation_candidate import ActivationCandidate


@dataclass(frozen=True)
class ValidationError:
    field: str = ""
    message: str = ""
    severity: str = "error"  # error, warning, info


@dataclass(frozen=True)
class ValidationReport:
    draft_id: str = ""
    valid: bool = False
    total_errors: int = 0
    total_warnings: int = 0
    errors: List[ValidationError] = field(default_factory=list)
    summary: str = ""


class ActivationValidator:
    """Memvalidasi ActivationDraft — rule-based, read-only."""

    VALID_TYPES = {"immediate", "scheduled", "conditional", "manual", "batch"}

    def validate(self, draft: ActivationDraft,
                 candidates: List[ActivationCandidate]) -> ValidationReport:
        errors: List[ValidationError] = []
        if not draft.draft_id:
            errors.append(ValidationError("draft_id", "Draft ID is empty", "error"))
        if not draft.context_id:
            errors.append(ValidationError("context_id", "Context ID is empty", "error"))
        if draft.candidates <= 0:
            errors.append(ValidationError("candidates", "No candidates in draft", "error"))
        if not draft.top_candidate:
            errors.append(ValidationError("top_candidate", "No top candidate selected", "warning"))

        for c in candidates:
            if c.candidate_type not in self.VALID_TYPES:
                errors.append(ValidationError(
                    c.candidate_id, f"Invalid type: {c.candidate_type}", "error"
                ))
            if not (0.0 <= c.confidence <= 1.0):
                errors.append(ValidationError(
                    c.candidate_id, f"Confidence out of range: {c.confidence}", "error"
                ))
            if not (0.0 <= c.priority_score <= 1.0):
                errors.append(ValidationError(
                    c.candidate_id, f"Priority out of range: {c.priority_score}", "warning"
                ))

        errs = [e for e in errors if e.severity == "error"]
        warns = [e for e in errors if e.severity == "warning"]
        return ValidationReport(
            draft_id=draft.draft_id,
            valid=len(errs) == 0 and draft.candidates > 0,
            total_errors=len(errs),
            total_warnings=len(warns),
            errors=errors,
            summary=f"{len(errs)} errors, {len(warns)} warnings",
        )
