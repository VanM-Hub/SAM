# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 129 - Coordination: coordination_validator.

Validates a coordination report.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .coordination_report import CoordinationReport
from .coordination_state import CoordinationState


@dataclass(frozen=True)
class CoordinationValidationIssue:
    message: str


@dataclass(frozen=True)
class CoordinationValidationReport:
    valid: bool
    issues: Tuple[CoordinationValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class CoordinationValidator:
    """Validates that all coordinated states are well-formed."""

    def validate(self, report: CoordinationReport) -> CoordinationValidationReport:
        issues = []
        for s in report.states:
            if not s.runtime_id:
                issues.append(CoordinationValidationIssue("empty runtime_id"))
            if s.state not in ("planned", "ready", "coordinated"):
                issues.append(
                    CoordinationValidationIssue("unknown state: {0}".format(s.state))
                )
        return CoordinationValidationReport(valid=not issues, issues=tuple(issues))
