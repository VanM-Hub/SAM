"""Conversation Builder Bridge — query read-only (Sprint 198)."""
from __future__ import annotations

from ..model.workflow import Workflow
from .workflow_builder import WorkflowBuilder
from .step_builder import StepBuilder
from .dependency_builder import DependencyBuilder
from .constraint_builder import ConstraintBuilder
from .preview_builder import PreviewBuilder


class ConversationBuilderBridge:
    """Bridge conversation — 5 query read-only builder workflow."""

    def __init__(self) -> None:
        self._wf = WorkflowBuilder()
        self._step = StepBuilder()
        self._dep = DependencyBuilder()
        self._cst = ConstraintBuilder()
        self._prev = PreviewBuilder()

    def query_1_workflow(self, workflow_id: str) -> Workflow:
        return self._wf.build(workflow_id).workflow

    def query_2_step(self, step_id: str, workflow_id: str):
        return self._step.build(step_id, workflow_id)

    def query_3_dependency(self, dep_id: str, fr: str, to: str):
        return self._dep.build(dep_id, fr, to)

    def query_4_constraint(self, constraint_id: str):
        return self._cst.build(constraint_id)

    def query_5_preview(self, label: str, workflow: Workflow):
        return self._prev.build(label, workflow)
