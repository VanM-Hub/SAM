# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 124 - Runtime Discovery: runtime_validator.

Validates that discovered runtimes are well-formed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .runtime_catalog import RuntimeCatalog
from .runtime_descriptor import RuntimeDescriptor


@dataclass(frozen=True)
class DiscoveryValidationIssue:
    runtime_id: str
    message: str


@dataclass(frozen=True)
class DiscoveryValidationReport:
    valid: bool
    issues: Tuple[DiscoveryValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class RuntimeValidator:
    """Validates runtime descriptors for well-formedness."""

    def __init__(self, catalog: RuntimeCatalog) -> None:
        self._catalog = catalog

    def validate(self) -> DiscoveryValidationReport:
        issues = []
        for d in self._catalog.all():
            if not d.runtime_id:
                issues.append(DiscoveryValidationIssue("?", "empty runtime_id"))
            if d.pipeline_position < 0:
                issues.append(
                    DiscoveryValidationIssue(d.runtime_id, "negative pipeline_position")
                )
        return DiscoveryValidationReport(
            valid=not issues,
            issues=tuple(issues),
        )
