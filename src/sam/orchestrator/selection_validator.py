# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 125 - Runtime Selection: selection_validator.

Validates a selection outcome for well-formedness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .runtime_selector import RuntimeSelection


@dataclass(frozen=True)
class SelectionValidationIssue:
    message: str


@dataclass(frozen=True)
class SelectionValidationReport:
    valid: bool
    issues: Tuple[SelectionValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class SelectionValidator:
    """Validates that a selection is well-formed."""

    def validate(self, selection: RuntimeSelection) -> SelectionValidationReport:
        issues = []
        seen = set()
        for rid in selection.chain:
            if rid in seen:
                issues.append(SelectionValidationIssue("duplicate runtime: {0}".format(rid)))
            seen.add(rid)
        return SelectionValidationReport(valid=not issues, issues=tuple(issues))
