"""Constraint Builder — membangun PolicyConstraint (Sprint 206)."""
from __future__ import annotations

from ..model.policy_constraint import PolicyConstraint


class ConstraintBuilder:
    """Builder batasan. Menyusun DTO deklaratif saja."""

    def build(self, constraint_id: str, kind: str = "condition", expression: str = "") -> PolicyConstraint:
        return PolicyConstraint(
            constraint_id=constraint_id, kind=kind, expression=expression,
        )
