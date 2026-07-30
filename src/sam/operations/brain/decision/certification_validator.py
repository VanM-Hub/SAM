"""
Certification Validator.

Validates certification integrity, evidence, rule completeness, decision consistency.
"""

from dataclasses import dataclass, field
from typing import List
from .approval_certification import ApprovalCertification, CertificationState


@dataclass(frozen=True)
class CertificationValidationResult:
    valid: bool = True; errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list); score: float = 1.0
    def to_dict(self) -> dict: return {"valid":self.valid,"errors":list(self.errors),"warnings":list(self.warnings),"score":self.score}


class CertificationValidator:
    def validate(self, cert: ApprovalCertification) -> CertificationValidationResult:
        errors=[]; warnings=[]
        if not cert.certification_id: errors.append("Missing certification ID")
        if not cert.activation_id: errors.append("Missing activation ID")
        if not cert.lifecycle_id: errors.append("Missing lifecycle ID")
        if not cert.requirements: warnings.append("No requirements evaluated")
        if cert.certified and cert.blocker_count > 0: warnings.append("Certified but has blockers")
        if cert.readiness_score < 0 or cert.readiness_score > 1.0:
            errors.append("Readiness score out of range")
        if cert.state == CertificationState.FAILED and cert.certified:
            errors.append("Failed but marked certified")
        return CertificationValidationResult(valid=len(errors)==0, errors=errors, warnings=warnings, score=max(0,1-len(errors)*0.3))
