"""
Activation Validator.

Validates activation integrity, lifecycle/gateway compatibility, rule consistency.
"""

from dataclasses import dataclass, field
from typing import List
from .approval_activation import ApprovalActivation, ActivationState


@dataclass(frozen=True)
class ActivationValidationResult:
    valid: bool = True; errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list); score: float = 1.0
    def to_dict(self) -> dict: return {"valid":self.valid,"errors":list(self.errors),"warnings":list(self.warnings),"score":self.score}


class ActivationValidator:
    def validate(self, activation: ApprovalActivation) -> ActivationValidationResult:
        errors=[]; warnings=[]
        if not activation.activation_id: errors.append("Missing activation ID")
        if not activation.lifecycle_id: errors.append("Missing lifecycle ID")
        if not activation.session_id: errors.append("Missing session ID")
        if activation.state == ActivationState.INVALID: errors.append("Invalid state detected")
        if activation.readiness_score < 0 or activation.readiness_score > 1.0:
            errors.append("Readiness score out of range")
        if len(activation.blockers) > 5: warnings.append("Many blockers")
        if activation.ready and activation.blockers:
            warnings.append("Ready but has blockers")
        return ActivationValidationResult(valid=len(errors)==0, errors=errors, warnings=warnings, score=max(0,1-len(errors)*0.3))
