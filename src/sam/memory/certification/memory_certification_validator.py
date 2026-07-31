"""Memory Certification Validator — validasi sertifikasi memori (Sprint 178).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MemoryCertificationValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class MemoryCertificationValidator:
    """Validator sertifikasi memori. Deterministik."""

    def validate(
        self,
        frozen: bool = True,
        synchronous: bool = True,
        preview_only: bool = True,
        no_write: bool = True,
        no_forbidden_imports: bool = True,
    ) -> MemoryCertificationValidation:
        issues = []
        if not frozen:
            issues.append("DTO not frozen")
        if not synchronous:
            issues.append("not synchronous")
        if not preview_only:
            issues.append("not preview-only")
        if not no_write:
            issues.append("write detected (filesystem/database)")
        if not no_forbidden_imports:
            issues.append("forbidden imports detected")
        return MemoryCertificationValidation(valid=not issues, issues=issues)
