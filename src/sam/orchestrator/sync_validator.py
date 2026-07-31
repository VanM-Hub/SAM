# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 130 - Synchronization: sync_validator.

Validates a synchronization snapshot.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .sync_snapshot import SyncSnapshot


@dataclass(frozen=True)
class SyncValidationIssue:
    message: str


@dataclass(frozen=True)
class SyncValidationReport:
    valid: bool
    issues: Tuple[SyncValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class SyncValidator:
    """Validates a sync snapshot is well-formed."""

    def validate(self, snapshot: SyncSnapshot) -> SyncValidationReport:
        issues = []
        seen = set()
        for s in snapshot.states:
            if not s.runtime_id:
                issues.append(SyncValidationIssue("empty runtime_id"))
            if s.runtime_id in seen:
                issues.append(SyncValidationIssue("duplicate runtime: {0}".format(s.runtime_id)))
            seen.add(s.runtime_id)
            if s.state not in ("pending", "synchronized"):
                issues.append(SyncValidationIssue("unknown state: {0}".format(s.state)))
        return SyncValidationReport(valid=not issues, issues=tuple(issues))
