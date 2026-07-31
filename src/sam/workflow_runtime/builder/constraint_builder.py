"""Constraint Builder — membangun WorkflowConstraint (Sprint 198)."""
from __future__ import annotations

from ..model.workflow_constraint import WorkflowConstraint


class ConstraintBuilder:
    """Builder batasan. Menyusun DTO deklaratif saja."""

    def build(self, constraint_id: str, kind: str = "order", expression: str = "") -> WorkflowConstraint:
        return WorkflowConstraint(
            constraint_id=constraint_id, kind=kind, expression=expression,
        )
