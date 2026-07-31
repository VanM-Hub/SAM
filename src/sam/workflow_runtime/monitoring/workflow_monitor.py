"""Workflow Monitor — pemantauan status workflow (Sprint 201)."""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.workflow_registry import WorkflowRegistry


@dataclass(frozen=True)
class WorkflowStatus:
    """Status workflow (immutable)."""
    workflow_id: str
    registered: bool = False
    healthy: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "healthy", self.registered)


class WorkflowMonitor:
    """Monitor workflow. Read-only, deterministik."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def status(self, workflow_id: str) -> WorkflowStatus:
        return WorkflowStatus(workflow_id, self._registry.exists(workflow_id))

    def all_status(self):
        return [self.status(d.id) for d in self._registry.all()]

    def healthy_count(self) -> int:
        return sum(1 for d in self._registry.all() if self._registry.exists(d.id))
