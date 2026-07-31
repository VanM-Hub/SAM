"""Workflow Certification Validator — validasi sertifikasi (Sprint 202)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class WorkflowCertificationValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class WorkflowCertificationValidator:
    """Validator sertifikasi workflow. Deterministik."""

    def validate(
        self,
        frozen: bool = True,
        synchronous: bool = True,
        preview_only: bool = True,
        no_write: bool = True,
        no_inference: bool = True,
        no_forbidden_imports: bool = True,
    ) -> WorkflowCertificationValidation:
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
        return WorkflowCertificationValidation(valid=not issues, issues=issues)
