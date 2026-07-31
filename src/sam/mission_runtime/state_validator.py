# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 139 - Mission State: state_validator.

Validates mission states and transitions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .mission_state import MissionState
from .state_transition import StateTransition


@dataclass(frozen=True)
class StateValidationIssue:
    message: str


@dataclass(frozen=True)
class StateValidationReport:
    valid: bool
    issues: Tuple[StateValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class StateValidator:
    """Validates that states are within the allowed set."""

    ALLOWED = ("open", "active", "closed")

    def validate_state(self, state: MissionState) -> StateValidationReport:
        issues = []
        if state.state not in self.ALLOWED:
            issues.append(StateValidationIssue("unknown state: {0}".format(state.state)))
        return StateValidationReport(valid=not issues, issues=tuple(issues))

    def validate_transition(self, t: StateTransition) -> StateValidationReport:
        issues = []
        if t.from_state not in self.ALLOWED:
            issues.append(StateValidationIssue("bad from-state: {0}".format(t.from_state)))
        if t.to_state not in self.ALLOWED:
            issues.append(StateValidationIssue("bad to-state: {0}".format(t.to_state)))
        return StateValidationReport(valid=not issues, issues=tuple(issues))
