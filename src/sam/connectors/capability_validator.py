"""Capability Validator — engine validasi kapabilitas.

Sprint 114 — Connector Capability.
Validasi kapabilitas terdaftar (read-only, deterministik).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class CapabilityValidationIssue:
    connector_id: str
    capability_id: str
    message: str
    severity: str = "warning"


@dataclass(frozen=True)
class CapabilityValidationReport:
    connector_id: str
    valid: bool = True
    issues: List[CapabilityValidationIssue] = field(default_factory=list)


class CapabilityValidator:
    """Validasi kapabilitas connector."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def validate(self, connector_id: str) -> CapabilityValidationReport:
        caps = self._registry.get_capabilities(connector_id)
        issues = []
        for cap in caps:
            if not cap.capability_id.strip():
                issues.append(CapabilityValidationIssue(
                    connector_id, cap.capability_id, "empty capability_id", "error"))
            if not cap.name.strip():
                issues.append(CapabilityValidationIssue(
                    connector_id, cap.capability_id, "empty name", "warning"))
        return CapabilityValidationReport(connector_id=connector_id,
                                          valid=not [i for i in issues if i.severity == "error"],
                                          issues=issues)
