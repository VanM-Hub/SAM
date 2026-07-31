"""Workflow Runtime Report — laporan runtime integrasi (Sprint 203)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.workflow_registry import WorkflowRegistry
from .workflow_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class WorkflowRuntimeReport:
    """Laporan runtime integrasi (immutable)."""
    total_workflow: int = 0
    route: List[str] = field(default_factory=list)
    external_calls: int = 0
    ready: bool = False


class WorkflowRuntimeReporter:
    """Reporter runtime integrasi. Read-only."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def report(self) -> WorkflowRuntimeReport:
        return WorkflowRuntimeReport(
            total_workflow=self._registry.count(),
            route=list(INTEGRATION_ROUTE),
            external_calls=0,
            ready=self._registry.count() > 0,
        )
