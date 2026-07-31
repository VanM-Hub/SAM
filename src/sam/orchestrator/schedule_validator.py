# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 128 - Scheduling: schedule_validator.

Validates a schedule plan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .schedule_plan import SchedulePlan


@dataclass(frozen=True)
class ScheduleValidationIssue:
    message: str


@dataclass(frozen=True)
class ScheduleValidationReport:
    valid: bool
    issues: Tuple[ScheduleValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class ScheduleValidator:
    """Validates a schedule plan for duplicates/emptiness."""

    def validate(self, plan: SchedulePlan) -> ScheduleValidationReport:
        issues = []
        if not plan.order:
            issues.append(ScheduleValidationIssue("empty schedule order"))
        seen = set()
        for rid in plan.order:
            if rid in seen:
                issues.append(ScheduleValidationIssue("duplicate runtime: {0}".format(rid)))
            seen.add(rid)
        return ScheduleValidationReport(valid=not issues, issues=tuple(issues))
