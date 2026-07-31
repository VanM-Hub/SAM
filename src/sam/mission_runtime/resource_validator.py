# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 137 - Mission Resources: resource_validator.

Validates a resource allocation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .resource_allocator import ResourceAllocation


@dataclass(frozen=True)
class ResourceValidationIssue:
    message: str


@dataclass(frozen=True)
class ResourceValidationReport:
    valid: bool
    issues: Tuple[ResourceValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class ResourceValidator:
    """Validates allocation is consistent."""

    def validate(self, allocation: ResourceAllocation) -> ResourceValidationReport:
        issues = []
        seen = set()
        for r in allocation.allocated:
            if r.resource_id in seen:
                issues.append(ResourceValidationIssue("duplicate: {0}".format(r.resource_id)))
            seen.add(r.resource_id)
        return ResourceValidationReport(valid=not issues, issues=tuple(issues))
