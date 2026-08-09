"""Recovery Explainability - WP-18 (MISSION-4.5 / IP-4.5-002).

Menjelaskan rencana pemulihan: alasan langkah, evidence, dan kebutuhan
approval. Read-only, auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .recovery_planning import RecoveryPlan


@dataclass(frozen=True)
class RecoveryExplanation:
    """Penjelasan rencana pemulihan."""

    plan_id: str
    investigation_id: str
    risk_level: str
    step_rationale: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    approval_required: bool = True

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "investigation_id": self.investigation_id,
            "risk_level": self.risk_level,
            "step_rationale": [list(s) for s in self.step_rationale],
            "approval_required": self.approval_required,
        }


class RecoveryExplainer:
    """Menjelaskan rencana pemulihan (read-only)."""

    def explain(self, plan: RecoveryPlan) -> RecoveryExplanation:
        step_rationale = tuple(
            (step.action, f"applies to {step.target_id} with rollback: {step.rollback}")
            for step in plan.steps
        )
        return RecoveryExplanation(
            plan_id=plan.plan_id,
            investigation_id=plan.investigation_id,
            risk_level=plan.risk_level,
            step_rationale=step_rationale,
            approval_required=plan.requires_approval,
        )
