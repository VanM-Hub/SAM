# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Mission validator (Sprint 135) + certification validator (Sprint 143).

Both validators live in one module because both sprints specify the file
name `mission_validator.py`. They validate disjoint concerns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .mission_definition import MissionDefinition
from .mission_certification import CertificationResult

# ---------------------------------------------------------------------------
# Sprint 135 - Mission Definition validation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MissionValidationIssue:
    message: str


@dataclass(frozen=True)
class MissionValidationReport:
    valid: bool
    issues: Tuple[MissionValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class MissionValidator:
    """Validates a mission definition for well-formedness."""

    def validate(self, definition: MissionDefinition) -> MissionValidationReport:
        issues = []
        if not definition.mission_id:
            issues.append(MissionValidationIssue("empty mission_id"))
        if not definition.metadata.version:
            issues.append(MissionValidationIssue("empty version"))
        if not definition.constraints.preview_only:
            issues.append(MissionValidationIssue("constraints not preview-only"))
        return MissionValidationReport(valid=not issues, issues=tuple(issues))


# ---------------------------------------------------------------------------
# Sprint 143 - Mission Certification validation
# ---------------------------------------------------------------------------


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
