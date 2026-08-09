"""Autonomous Investigation Explainability - WP-08 (MISSION-4.5 / IP-4.5-001).

Menjelaskan seluruh proses Autonomous Investigation beserta evidence yang
digunakan. Evidence chain lengkap, explainability dapat diaudit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .autonomous_investigation import AutonomousInvestigation
from .investigation_planning import InvestigationPlan


@dataclass(frozen=True)
class TriggerExplanation:
    """Penjelasan pemicu."""

    reason: str
    severity: str
    source_request_id: str = ""

    def as_dict(self) -> dict:
        return {
            "reason": self.reason,
            "severity": self.severity,
            "source_request_id": self.source_request_id,
        }


@dataclass(frozen=True)
class PlanningExplanation:
    """Penjelasan perencanaan."""

    plan_id: str
    priority: str
    step_rationale: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "priority": self.priority,
            "step_rationale": [list(s) for s in self.step_rationale],
        }


@dataclass(frozen=True)
class AutonomousInvestigationExplanation:
    """Penjelasan penuh sebuah investigasi otonom."""

    investigation_id: str
    reason: str
    trigger: TriggerExplanation
    planning: PlanningExplanation
    evidence_chain: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "reason": self.reason,
            "trigger": self.trigger.as_dict(),
            "planning": self.planning.as_dict(),
            "evidence_chain": list(self.evidence_chain),
        }


class AutonomousInvestigationExplainer:
    """Menjelaskan investigasi otonom (read-only)."""

    def explain(
        self,
        investigation: AutonomousInvestigation,
        plan: InvestigationPlan,
    ) -> AutonomousInvestigationExplanation:
        trigger = TriggerExplanation(
            reason=investigation.reason,
            severity=investigation.targets[0] if investigation.targets else "n/a",
            source_request_id=investigation.request_id,
        )
        planning = PlanningExplanation(
            plan_id=plan.plan_id,
            priority=plan.priority,
            step_rationale=tuple((step, f"perform {step}") for step, _ in plan.steps),
        )
        evidence_chain = tuple(
            dict.fromkeys(("trigger", "context", "runtime", "provider", "plan"))
        )
        return AutonomousInvestigationExplanation(
            investigation_id=investigation.investigation_id,
            reason=investigation.reason,
            trigger=trigger,
            planning=planning,
            evidence_chain=evidence_chain,
        )
