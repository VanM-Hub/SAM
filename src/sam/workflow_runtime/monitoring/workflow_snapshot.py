"""Workflow Snapshot — snapshot workflow (Sprint 201)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.workflow_registry import WorkflowRegistry


@dataclass(frozen=True)
class WorkflowSnapshot:
    """Snapshot workflow (immutable)."""
    total: int = 0
    scope_counts: Dict[str, int] = field(default_factory=dict)


class WorkflowSnapshotter:
    """Snapshotter workflow. Read-only."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def snapshot(self) -> WorkflowSnapshot:
        descs = self._registry.all()
        counts = {}
        for d in descs:
            counts[d.category] = counts.get(d.category, 0) + 1
        return WorkflowSnapshot(total=len(descs), scope_counts=counts)
