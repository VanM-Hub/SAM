# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 127 - Dependency Resolver: dependency_validator.

Validates a resolved dependency order.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .dependency_graph import DependencyGraph
from .dependency_resolver import DependencyResolver


@dataclass(frozen=True)
class DependencyValidationIssue:
    message: str


@dataclass(frozen=True)
class DependencyValidationReport:
    valid: bool
    issues: Tuple[DependencyValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class DependencyValidator:
    """Validates the dependency graph resolves cleanly."""

    def __init__(self, graph: DependencyGraph) -> None:
        self._resolver = DependencyResolver(graph)

    def validate(self) -> DependencyValidationReport:
        try:
            self._resolver.resolve()
            return DependencyValidationReport(valid=True)
        except ValueError as exc:
            return DependencyValidationReport(
                valid=False,
                issues=(DependencyValidationIssue(str(exc)),),
            )
