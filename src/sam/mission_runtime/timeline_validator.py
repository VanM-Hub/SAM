# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 138 - Mission Timeline: timeline_validator.

Validates a mission timeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .mission_timeline import MissionTimeline


@dataclass(frozen=True)
class TimelineValidationIssue:
    message: str


@dataclass(frozen=True)
class TimelineValidationReport:
    valid: bool
    issues: Tuple[TimelineValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class TimelineValidator:
    """Validates timeline ordering is sequential."""

    def validate(self, timeline: MissionTimeline) -> TimelineValidationReport:
        issues = []
        for idx, cp in enumerate(timeline.checkpoints):
            if cp.order != idx:
                issues.append(
                    TimelineValidationIssue(
                        "checkpoint {0} order mismatch".format(cp.checkpoint_id)
                    )
                )
        return TimelineValidationReport(valid=not issues, issues=tuple(issues))
