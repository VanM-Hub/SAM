"""Workflow Statistics — statistika runtime workflow (Sprint 199)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.workflow_registry import WorkflowRegistry


@dataclass(frozen=True)
class WorkflowStatisticsItem:
    """Statistik per unit (immutable)."""
    workflow_id: str = ""
    registered: bool = False


@dataclass(frozen=True)
class WorkflowStatistics:
    """Statistik workflow (immutable)."""
    total: int = 0
    registered: int = 0
    items: List[WorkflowStatisticsItem] = field(default_factory=list)


class WorkflowStatisticsCollector:
    """Collector statistik. Read-only."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def collect(self) -> WorkflowStatistics:
        descs = self._registry.all()
        items = [
            WorkflowStatisticsItem(workflow_id=d.id, registered=True)
            for d in descs
        ]
        return WorkflowStatistics(total=len(items), registered=len(items), items=items)
