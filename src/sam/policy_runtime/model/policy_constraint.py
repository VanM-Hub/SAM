"""Policy Constraint — batasan policy (Sprint 205)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyConstraint:
    """Batasan policy (immutable)."""
    constraint_id: str
    policy_id: str = ""
    kind: str = "condition"
    expression: str = ""
    preview_only: bool = True
