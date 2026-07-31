"""Workflow Constraint — batasan workflow (Sprint 197)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowConstraint:
    """Batasan workflow (immutable)."""
    constraint_id: str
    workflow_id: str = ""
    kind: str = "order"
    expression: str = ""
    preview_only: bool = True

    def is_satisfied(self) -> bool:
        # Workflow constraint bersifat deklaratif: selalu dianggap valid
        # pada tahap model (validasi nyata di layer lain).
        return True
