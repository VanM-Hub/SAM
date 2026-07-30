"""
Lifecycle Validator.

Validates lifecycle transitions, consistency, and integrity.
"""

from typing import List
from dataclasses import dataclass, field
from .approval_lifecycle import ApprovalLifecycle, ApprovalLifecycleState
from .lifecycle_rules import LifecycleRules


@dataclass(frozen=True)
class LifecycleValidationResult:
    valid: bool = True; errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list); score: float = 1.0
    def to_dict(self) -> dict: return {"valid":self.valid,"errors":list(self.errors),"warnings":list(self.warnings),"score":self.score}


class LifecycleValidator:
    def validate(self, lifecycle: ApprovalLifecycle) -> LifecycleValidationResult:
        errors=[]; warnings=[]
        if not lifecycle.lifecycle_id: errors.append("Missing lifecycle ID")
        if not lifecycle.session_id: errors.append("Missing session ID")
        for t in lifecycle.transitions:
            if not LifecycleRules.can_transition(t.from_state, t.to_state):
                errors.append(f"Illegal transition: {t.from_state} → {t.to_state}")
        if len(lifecycle.transitions) > 20: warnings.append("Many transitions detected")
        return LifecycleValidationResult(valid=len(errors)==0, errors=errors, warnings=warnings, score=max(0,1-len(errors)*0.3))
