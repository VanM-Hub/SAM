"""Workflow Health — kesehatan runtime workflow (Sprint 201)."""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.workflow_registry import WorkflowRegistry


@dataclass(frozen=True)
class WorkflowHealth:
    """Kesehatan workflow (immutable)."""
    total: int = 0
    healthy_workflow: int = 0

    @property
    def healthy(self) -> bool:
        return self.healthy_workflow == self.total


class WorkflowHealthCheck:
    """Health check workflow. Read-only."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def check(self) -> WorkflowHealth:
        total = self._registry.count()
        healthy = sum(1 for d in self._registry.all() if self._registry.exists(d.id))
        return WorkflowHealth(total=total, healthy_workflow=healthy)
