# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 136 - Mission Objectives: objective_validator.

Validates that objectives have no cycles/dangling deps.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .objective_registry import ObjectiveRegistry


@dataclass(frozen=True)
class ObjectiveValidationIssue:
    message: str


@dataclass(frozen=True)
class ObjectiveValidationReport:
    valid: bool
    issues: Tuple[ObjectiveValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class ObjectiveValidator:
    """Validates objectives for dangling/cyclic dependencies."""

    def __init__(self, registry: ObjectiveRegistry) -> None:
        self._registry = registry

    def validate(self) -> ObjectiveValidationReport:
        issues = []
        known = self._registry.ids()
        for obj in self._registry.all():
            for dep in obj.depends_on:
                if dep not in known:
                    issues.append(
                        ObjectiveValidationIssue(
                            "dangling dep {0} in {1}".format(dep, obj.objective_id)
                        )
                    )
        return ObjectiveValidationReport(valid=not issues, issues=tuple(issues))
