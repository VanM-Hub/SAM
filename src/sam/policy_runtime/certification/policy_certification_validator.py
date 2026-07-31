"""Policy Certification Validator — validasi sertifikasi (Sprint 210)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class PolicyCertificationValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class PolicyCertificationValidator:
    """Validator sertifikasi policy. Deterministik."""

    def validate(
        self,
        frozen: bool = True,
        synchronous: bool = True,
        preview_only: bool = True,
        no_write: bool = True,
        no_inference: bool = True,
        no_forbidden_imports: bool = True,
    ) -> PolicyCertificationValidation:
        issues = []
        if not frozen:
            issues.append("DTO not frozen")
        if not synchronous:
            issues.append("not synchronous")
        if not preview_only:
            issues.append("not preview-only")
        if not no_write:
            issues.append("write detected (filesystem/database)")
        if not no_inference:
            issues.append("inference detected")
        if not no_forbidden_imports:
            issues.append("forbidden imports detected")
        return PolicyCertificationValidation(valid=not issues, issues=issues)
