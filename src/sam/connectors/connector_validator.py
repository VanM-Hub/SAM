"""Connector Validator — engine validasi connector (preview-only).

Sprint 113 — Connector Discovery.
Validasi integritas deskripsi connector secara deterministik, read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_registry import ConnectorRegistry
from .connector_descriptor import ConnectorDescriptor


@dataclass(frozen=True)
class ValidationIssue:
    """Isu validasi individual (immutable)."""
    field_name: str
    message: str
    severity: str = "warning"  # info | warning | error


@dataclass(frozen=True)
class ValidationReport:
    """Laporan validasi connector (immutable)."""
    connector_id: str
    valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")


class ConnectorValidator:
    """Validasi integritas connector."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def validate(self, connector_id: str) -> ValidationReport:
        d = self._registry.get(connector_id)
        if d is None:
            return ValidationReport(connector_id=connector_id, valid=False,
                                    issues=[ValidationIssue("connector", "not found", "error")])
        issues: List[ValidationIssue] = []
        if not d.connector_id.strip():
            issues.append(ValidationIssue("connector_id", "empty", "error"))
        if not d.name.strip():
            issues.append(ValidationIssue("name", "empty", "error"))
        if not d.connector_type.strip():
            issues.append(ValidationIssue("connector_type", "empty", "warning"))
        return ValidationReport(connector_id=connector_id, valid=not issues,
                                issues=issues)

    def validate_all(self) -> List[ValidationReport]:
        return [self.validate(cid) for cid in self._registry.list_ids()]
