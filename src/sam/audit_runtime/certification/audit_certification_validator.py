"""Audit Certification Validator — validasi sertifikasi audit (Sprint 218)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AuditCertificationValidation:
    """Hasil validasi immutable."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class AuditCertificationValidator:
    """Validator sertifikasi audit — menegakkan konstrain."""

    def validate(self, no_write: bool = True, no_inference: bool = True,
                 frozen: bool = True, no_execute: bool = True,
                 external_calls: int = 0) -> AuditCertificationValidation:
        issues = []
        if not no_write:
            issues.append("write detected (filesystem/database)")
        if not no_inference:
            issues.append("inference detected (no AI/LLM)")
        if not frozen:
            issues.append("mutable DTO detected")
        if not no_execute:
            issues.append("execute detected (preview-only)") 
        if external_calls != 0:
            issues.append("external_calls must be 0")
        return AuditCertificationValidation(
            valid=len(issues) == 0, issues=issues)
