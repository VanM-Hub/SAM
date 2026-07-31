# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 140 - Mission Coordination: coordination_validator.

Validates a coordination plan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .coordination_plan import CoordinationPlan


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
    """Validates a coordination plan is well-formed."""

    def validate(self, plan: CoordinationPlan) -> CoordinationValidationReport:
        issues = []
        seen = set()
        for rid in plan.runtimes:
            if rid in seen:
                issues.append(
                    CoordinationValidationIssue("duplicate runtime: {0}".format(rid))
                )
            seen.add(rid)
        return CoordinationValidationReport(valid=not issues, issues=tuple(issues))
