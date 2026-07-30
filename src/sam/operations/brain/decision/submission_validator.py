"""
Submission Validator.

Validates submission plans. Rule-based. Deterministic.
"""

from typing import List
from dataclasses import dataclass, field
from .submission_plan import ApprovalSubmissionPlan


@dataclass(frozen=True)
class SubmissionValidationResult:
    valid: bool = True; errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list); score: float = 1.0
    def to_dict(self) -> dict: return {"valid":self.valid,"errors":list(self.errors),"warnings":list(self.warnings),"score":self.score}


class SubmissionValidator:
    def validate(self, plan: ApprovalSubmissionPlan) -> SubmissionValidationResult:
        errors = []; warnings = []
        if not plan.plan_id: errors.append("Missing plan ID")
        if not plan.envelope_id: errors.append("Missing envelope ID")
        if not plan.metadata: errors.append("Missing metadata")
        if plan.metadata and not plan.metadata.submission_id: warnings.append("No submission ID")
        if not plan.stages: warnings.append("No stages defined")
        if not plan.references: warnings.append("No references")
        return SubmissionValidationResult(valid=len(errors)==0, errors=errors, warnings=warnings,
                                           score=max(0, 1-len(errors)*0.3))
