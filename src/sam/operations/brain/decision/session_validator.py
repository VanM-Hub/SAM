"""
Session Validator.

Validates approval sessions. Rule-based. Deterministic.
"""

from typing import List
from dataclasses import dataclass, field
from .approval_session import ApprovalSession


@dataclass(frozen=True)
class SessionValidationResult:
    valid: bool = True; errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list); score: float = 1.0
    def to_dict(self) -> dict: return {"valid":self.valid,"errors":list(self.errors),"warnings":list(self.warnings),"score":self.score}


class SessionValidator:
    def validate(self, session: ApprovalSession) -> SessionValidationResult:
        errors=[]; warnings=[]
        if not session.session_id: errors.append("Missing session ID")
        if not session.references: warnings.append("No references")
        if not session.metadata: warnings.append("No metadata")
        if session.references and not session.references.gateway_request_id: warnings.append("No gateway reference")
        return SessionValidationResult(valid=len(errors)==0, errors=errors, warnings=warnings, score=max(0,1-len(errors)*0.3))
