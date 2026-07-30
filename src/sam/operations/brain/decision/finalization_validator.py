"""
Finalization Validator.

Validates final decision record completeness, pipeline integrity, and consistency.
"""

from dataclasses import dataclass, field
from typing import List
from .finalization import FinalDecisionRecord, FinalDecisionState


@dataclass(frozen=True)
class FinalizationValidationResult:
    valid: bool = True; errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list); score: float = 1.0
    def to_dict(self) -> dict: return {"valid":self.valid,"errors":list(self.errors),"warnings":list(self.warnings),"score":self.score}


class FinalizationValidator:
    def validate(self, record: FinalDecisionRecord) -> FinalizationValidationResult:
        errors=[]; warnings=[]
        if not record.record_id: errors.append("Missing record ID")
        if not record.session_id: errors.append("Missing session ID")
        if not record.lifecycle_id: errors.append("Missing lifecycle ID")
        if not record.activation_id: errors.append("Missing activation ID")
        if not record.certification_id: errors.append("Missing certification ID")
        if record.state == FinalDecisionState.PENDING and record.complete:
            warnings.append("Complete but state is PENDING")
        if record.pipeline_integrity < 0 or record.pipeline_integrity > 1.0:
            errors.append("Integrity out of range")
        if not record.summary: warnings.append("No summary")
        if not record.metadata: warnings.append("No metadata")
        return FinalizationValidationResult(valid=len(errors)==0, errors=errors, warnings=warnings, score=max(0,1-len(errors)*0.3))
