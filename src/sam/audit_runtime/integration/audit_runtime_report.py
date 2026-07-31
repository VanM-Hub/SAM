"""Audit Runtime Report — laporan runtime integrasi (Sprint 219)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.audit_registry import AuditRegistry
from .audit_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class AuditRuntimeReport:
    """Laporan runtime integrasi (immutable)."""
    total_audit: int = 0
    route: List[str] = field(default_factory=list)
    external_calls: int = 0
    ready: bool = False


class AuditRuntimeReporter:
    """Reporter runtime integrasi. Read-only."""

    def __init__(self, registry: AuditRegistry) -> None:
        self._registry = registry

    def report(self) -> AuditRuntimeReport:
        return AuditRuntimeReport(
            total_audit=self._registry.count(),
            route=list(INTEGRATION_ROUTE),
            external_calls=0,
            ready=self._registry.count() > 0,
        )
