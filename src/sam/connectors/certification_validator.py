"""Certification Validator — engine validasi sertifikasi.

Sprint 122 — Connector Certification.
Validasi hasil sertifikasi (read-only).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_certification import CertificationResult


@dataclass(frozen=True)
class CertificationValidation:
    """Hasil validasi sertifikasi."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class CertificationValidator:
    """Validasi hasil sertifikasi."""

    def validate(self, result: CertificationResult) -> CertificationValidation:
        issues = []
        if result.certified and result.score < 100.0:
            issues.append("certified but score < 100")
        if not result.criteria:
            issues.append("no criteria assessed")
        return CertificationValidation(not issues, issues)
