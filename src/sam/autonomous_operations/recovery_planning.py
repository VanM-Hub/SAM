"""Recovery Planning + Validation - WP-11/12 (MISSION-4.5 / IP-4.5-002).

Menyusun & memvalidasi rencana pemulihan operasional. Plan & validation
read-only; tidak melakukan recovery itu sendiri (eksekusi di WP-13,
approval-gated).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class RecoveryStep:
    """Satu langkah pemulihan."""

    step_id: str
    action: str
    target_id: str = ""
    rollback: str = ""

    def as_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "target_id": self.target_id,
            "rollback": self.rollback,
        }


@dataclass(frozen=True)
class RecoveryPlan:
    """Rencana pemulihan."""

    plan_id: str
    investigation_id: str
    steps: Tuple[RecoveryStep, ...] = field(default_factory=tuple)
    risk_level: str = "low"  # low | medium | high
    requires_approval: bool = True
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "investigation_id": self.investigation_id,
            "steps": [s.as_dict() for s in self.steps],
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class RecoveryValidation:
    """Hasil validasi rencana pemulihan."""

    plan_id: str
    valid: bool
    reasons: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "valid": self.valid,
            "reasons": [list(r) for r in self.reasons],
        }


class RecoveryPlanner:
    """Planner pemulihan (deterministik, evidence-informed)."""

    def plan(
        self,
        investigation_id: str,
        *,
        detected_issues: Tuple[str, ...] = ("degraded",),
        severity: str = "warning",
    ) -> RecoveryPlan:
        steps = []
        for idx, issue in enumerate(detected_issues, start=1):
            action = self._action_for(issue)
            steps.append(
                RecoveryStep(
                    step_id=f"rx-{idx}",
                    action=action,
                    target_id=issue,
                    rollback=f"restore {issue} snapshot",
                )
            )
        risk_level = "high" if severity == "critical" else (
            "medium" if severity == "warning" else "low"
        )
        return RecoveryPlan(
            plan_id=uuid.uuid4().hex,
            investigation_id=investigation_id,
            steps=tuple(steps),
            risk_level=risk_level,
            requires_approval=True,
        )

    @staticmethod
    def _action_for(issue: str) -> str:
        text = issue.lower()
        if "restart" in text or "provider" in text:
            return "restart provider service"
        if "resource" in text or "cpu" in text or "memory" in text:
            return "rebalance resource allocation"
        if "network" in text:
            return "restore network connectivity"
        return "apply standard recovery"


class RecoveryValidator:
    """Memvalidasi rencana pemulihan (harus punya langkah & approval)."""

    @staticmethod
    def validate(plan: RecoveryPlan) -> RecoveryValidation:
        reasons: List[Tuple[str, str]] = []
        valid = True
        if not plan.steps:
            valid = False
            reasons.append(("no_steps", "recovery plan has no steps"))
        if not plan.requires_approval:
            valid = False
            reasons.append(("no_approval", "recovery must require approval"))
        if valid:
            reasons.append(("valid", "plan is safe to submit"))
        return RecoveryValidation(
            plan_id=plan.plan_id, valid=valid, reasons=tuple(reasons)
        )
