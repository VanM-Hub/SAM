"""
Approval Validator.

Validates ApprovalPreparation completeness.
Rule-based. Deterministic.
"""

from typing import List
from dataclasses import dataclass, field

from .approval_preparation import ApprovalPreparation


@dataclass(frozen=True)
class ApprovalValidationResult:
    valid: bool = True; errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list); score: float = 1.0
    def to_dict(self) -> dict:
        return {"valid":self.valid,"errors":list(self.errors),"warnings":list(self.warnings),"score":self.score}


class ApprovalValidator:
    """Validates approval preparation."""

    def validate(self, prep: ApprovalPreparation) -> ApprovalValidationResult:
        errors = []; warnings = []

        # Plan completeness
        if not prep.metadata:
            errors.append("Missing approval metadata")
        if not prep.candidates:
            errors.append("No approval candidates")

        # Required evidence
        if prep.metadata and not prep.metadata.plan_id:
            warnings.append("No plan ID in metadata")
        if prep.metadata and not prep.metadata.evaluation_id:
            warnings.append("No evaluation ID in metadata")

        # Required justification
        req_names = {r.name for r in prep.requirements}
        mandatory = {"plan_complete", "strategy_defined", "constraints_checked", "recommended_alternative"}
        missing = mandatory - req_names
        if missing:
            errors.append(f"Missing required requirements: {missing}")

        # Required policy
        if prep.metadata and prep.metadata.strategy_approach == "unknown":
            warnings.append("Strategy approach not determined")

        # Required constraints
        all_satisfied = all(r.satisfied for r in prep.requirements)
        if not all_satisfied:
            warnings.append("Not all requirements satisfied")

        # Integrity
        if prep.ready_for_submission and not all_satisfied:
            errors.append("Marked ready but not all requirements satisfied")

        valid = len(errors) == 0
        score = max(0.0, 1.0 - (len(errors) * 0.4 + len(warnings) * 0.1))
        return ApprovalValidationResult(valid=valid, errors=errors, warnings=warnings, score=round(score, 2))
