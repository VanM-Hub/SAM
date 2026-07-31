"""Step Builder — membangun WorkflowStep (Sprint 198)."""
from __future__ import annotations

from ..model.workflow_step import WorkflowStep


class StepBuilder:
    """Builder langkah. Menyusun DTO saja."""

    def build(self, step_id: str, workflow_id: str, order: int = 0) -> WorkflowStep:
        return WorkflowStep(step_id=step_id, workflow_id=workflow_id, order=order)
