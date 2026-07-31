"""Conversation Model Bridge — query read-only (Sprint 197)."""
from __future__ import annotations

from .workflow import Workflow
from .workflow_step import WorkflowStep
from .workflow_dependency import WorkflowDependency
from .workflow_constraint import WorkflowConstraint
from .workflow_validator import WorkflowValidator


class ConversationModelBridge:
    """Bridge conversation — query model workflow read-only."""

    def __init__(self) -> None:
        self._validator = WorkflowValidator()

    def build_workflow(self, workflow_id: str, name: str = "") -> Workflow:
        return Workflow(workflow_id=workflow_id, name=name)

    def build_step(self, step_id: str, workflow_id: str) -> WorkflowStep:
        return WorkflowStep(step_id=step_id, workflow_id=workflow_id)

    def is_valid(self, workflow: Workflow) -> bool:
        return self._validator.validate_workflow(workflow).valid

    def summary(self, workflow: Workflow) -> dict:
        return {
            "workflow_id": workflow.workflow_id,
            "step_count": workflow.step_count(),
        }
