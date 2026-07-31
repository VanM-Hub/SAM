# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 133 - Certification: orchestration_validator.

Validates certification results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .orchestration_certification import CertificationResult


@dataclass(frozen=True)
class CertificationValidationIssue:
    message: str


@dataclass(frozen=True)
class CertificationValidation:
    valid: bool
    issues: Tuple[CertificationValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class CertificationValidator:
    """Validates a certification result is self-consistent."""

    def validate(self, result: CertificationResult) -> CertificationValidation:
        issues = []
        if result.certified and result.met_count != result.total:
            issues.append(
                CertificationValidationIssue(
                    "certified but not all criteria met ({0}/{1})".format(
                        result.met_count, result.total
                    )
                )
            )
        return CertificationValidation(valid=not issues, issues=tuple(issues))
