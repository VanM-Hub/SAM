"""Workflow Metrics — metrik workflow (Sprint 201)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.workflow_registry import WorkflowRegistry


@dataclass(frozen=True)
class WorkflowMetricSample:
    """Sampel metrik per unit (immutable)."""
    workflow_id: str = ""
    registered: bool = False
    preview_count: int = 0
    external_calls: int = 0


@dataclass(frozen=True)
class WorkflowMetrics:
    """Metrik workflow agregat (immutable)."""
    total: int = 0
    external_calls: int = 0
    samples: List[WorkflowMetricSample] = field(default_factory=list)


class WorkflowMetricsCollector:
    """Collector metrik. Read-only."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def collect(self) -> WorkflowMetrics:
        samples = [
            WorkflowMetricSample(workflow_id=d.id, registered=True,
                                 preview_count=0, external_calls=0)
            for d in self._registry.all()
        ]
        return WorkflowMetrics(total=len(samples), external_calls=0, samples=samples)
