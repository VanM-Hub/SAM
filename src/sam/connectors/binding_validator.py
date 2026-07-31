"""Binding Validator — engine validasi binding.

Sprint 115 — Connector Binding.
Validasi binding request sebelum diproses (read-only, deterministik).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .binding_request import BindingRequest
from .connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class BindingValidationReport:
    request_id: str
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class BindingValidator:
    """Validasi permintaan binding."""

    def __init__(self, connector_registry: ConnectorRegistry) -> None:
        self._connectors = connector_registry

    def validate(self, request: BindingRequest) -> BindingValidationReport:
        issues = []
        if not request.request_id.strip():
            issues.append("request_id empty")
        if request.connector_id not in self._connectors.list_ids():
            issues.append("connector not registered")
        if not request.capability_ids:
            issues.append("no capabilities requested")
        return BindingValidationReport(request.request_id, valid=not issues, issues=issues)
