"""Workflow Report — laporan pemantauan workflow (Sprint 201)."""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.workflow_registry import WorkflowRegistry


@dataclass(frozen=True)
class WorkflowReport:
    """Laporan workflow (immutable)."""
    total: int = 0
    healthy: int = 0
    external_calls: int = 0


class WorkflowReporter:
    """Reporter workflow. Read-only."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def report(self) -> WorkflowReport:
        total = self._registry.count()
        return WorkflowReport(total=total, healthy=total, external_calls=0)
