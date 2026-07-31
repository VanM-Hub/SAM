"""Workflow Validator — validasi model workflow (Sprint 197)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .workflow import Workflow
from .workflow_step import WorkflowStep
from .workflow_dependency import WorkflowDependency
from .workflow_constraint import WorkflowConstraint


@dataclass(frozen=True)
class WorkflowValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class WorkflowValidator:
    """Validator model workflow. Deterministik, read-only."""

    def validate_workflow(self, workflow: Workflow) -> WorkflowValidation:
        issues = []
        if not workflow.workflow_id:
            issues.append("workflow_id is required")
        return WorkflowValidation(valid=not issues, issues=issues)

    def validate_step(self, step: WorkflowStep) -> WorkflowValidation:
        issues = []
        if not step.step_id:
            issues.append("step_id is required")
        if not step.workflow_id:
            issues.append("workflow_id is required")
        return WorkflowValidation(valid=not issues, issues=issues)

    def validate_dependency(self, dep: WorkflowDependency) -> WorkflowValidation:
        issues = []
        if not dep.ok():
            issues.append("dependency needs from_step and to_step")
        return WorkflowValidation(valid=not issues, issues=issues)

    def validate_constraint(self, constraint: WorkflowConstraint) -> WorkflowValidation:
        issues = []
        if not constraint.constraint_id:
            issues.append("constraint_id is required")
        return WorkflowValidation(valid=not issues, issues=issues)
