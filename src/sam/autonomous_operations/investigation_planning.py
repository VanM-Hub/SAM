"""Investigation Planning - WP-06 (MISSION-4.5 / IP-4.5-001).

Menyusun rencana investigasi secara deterministik berdasarkan evidence.
Plan selalu dihasilkan, berbasis evidence, prioritas dapat dijelaskan,
tidak melakukan execution.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Tuple


def _now_utc() -> str:
    return __import__("datetime").datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class InvestigationPlan:
    """Rencana investigasi (deterministik)."""

    plan_id: str
    investigation_id: str
    priority: str = "normal"  # high | medium | low
    steps: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "investigation_id": self.investigation_id,
            "priority": self.priority,
            "steps": [list(s) for s in self.steps],
            "evidence_ids": list(self.evidence_ids),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class PlanningExplanation:
    """Penjelasan perencanaan."""

    plan_id: str
    priority_reason: str
    step_rationale: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "priority_reason": self.priority_reason,
            "step_rationale": [list(s) for s in self.step_rationale],
        }


class InvestigationPlanner:
    """Planner investigasi (deterministik, evidence-based)."""

    def plan(
        self,
        investigation_id: str,
        *,
        severity: str = "warning",
        evidence_count: int = 0,
        critical_findings: int = 0,
    ) -> InvestigationPlan:
        priority = self._priority(severity, critical_findings)
        steps = (
            ("scope", "define investigation scope"),
            ("context", "collect operational context"),
            ("verify_runtime", "verify runtime condition"),
            ("verify_provider", "verify provider condition"),
            ("analyze", "compile evidence & conclusion"),
        )
        evidence_ids = tuple(
            f"evidence-{i}" for i in range(1, evidence_count + 1)
        ) or (f"source-{investigation_id[:8]}",)
        return InvestigationPlan(
            plan_id=uuid.uuid4().hex,
            investigation_id=investigation_id,
            priority=priority,
            steps=steps,
            evidence_ids=evidence_ids,
        )

    @staticmethod
    def _priority(severity: str, critical_findings: int) -> str:
        if severity == "critical" or critical_findings > 0:
            return "high"
        if severity == "warning":
            return "medium"
        return "low"

    def explain(self, plan: InvestigationPlan) -> PlanningExplanation:
        priority_reason = {
            "high": "critical severity or critical findings detected",
            "medium": "warning severity condition",
            "low": "informational condition",
        }.get(plan.priority, "normal condition")
        step_rationale = tuple(
            (step, f"perform {step} phase") for step, _ in plan.steps
        )
        return PlanningExplanation(
            plan_id=plan.plan_id,
            priority_reason=priority_reason,
            step_rationale=step_rationale,
        )
