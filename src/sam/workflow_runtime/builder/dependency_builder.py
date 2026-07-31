"""Dependency Builder — membangun WorkflowDependency (Sprint 198)."""
from __future__ import annotations

from ..model.workflow_dependency import WorkflowDependency


class DependencyBuilder:
    """Builder dependensi. Menyusun DTO saja — tidak resolusi."""

    def build(self, dependency_id: str, from_step: str, to_step: str) -> WorkflowDependency:
        return WorkflowDependency(
            dependency_id=dependency_id, from_step=from_step, to_step=to_step,
        )
