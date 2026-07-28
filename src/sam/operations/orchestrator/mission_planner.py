"""
OP-274 — Mission Planner

Gabungkan proposal menjadi MissionPlan.

MissionPlan berisi:
  - ordered proposals (by priority)
  - dependencies
  - blockers
  - estimated duration
  - required approvals
  - expected outcome

Belum membuat Mission.
Output adalah Plan / DTO saja.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timedelta


@dataclass(frozen=True)
class PlannedStep:
    proposal_id: str
    title: str
    priority_score: float
    dependencies: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    estimated_minutes: float = 30.0
    required_approvals: tuple[str, ...] = ()
    expected_outcome: str = ""
    severity: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "priority_score": self.priority_score,
            "dependencies": list(self.dependencies),
            "blockers": list(self.blockers),
            "estimated_minutes": self.estimated_minutes,
            "required_approvals": list(self.required_approvals),
            "expected_outcome": self.expected_outcome,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class MissionPlan:
    plan_id: str
    name: str
    steps: tuple[PlannedStep, ...]
    total_steps: int = 0
    total_estimated_minutes: float = 0.0
    total_approvals_needed: int = 0
    critical_count: int = 0
    blocker_count: int = 0
    created_at: str = ""
    description: str = ""

    @property
    def ordered_ids(self) -> list[str]:
        return [s.proposal_id for s in self.steps]

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "total_steps": self.total_steps,
            "total_estimated_minutes": self.total_estimated_minutes,
            "total_approvals_needed": self.total_approvals_needed,
            "critical_count": self.critical_count,
            "blocker_count": self.blocker_count,
            "created_at": self.created_at,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "ordered_ids": self.ordered_ids,
        }


class MissionPlanner:
    """
    Menyusun proposal menjadi MissionPlan yang terstruktur.

    Input: proposal list (dengan priority, dependency, blocker info)
    Output: MissionPlan DTO

    Tidak membuat Mission, tidak submit ke MissionController.
    """

    def plan(self,
             proposals: list[dict[str, Any]],
             plan_id: str | None = None,
             name: str = "",
             description: str = "",
             ) -> MissionPlan:
        """
        Susun proposal menjadi MissionPlan.

        Proposal dict keys:
          - id (required)
          - title (optional)
          - priority_score (optional, float)
          - depends_on (optional, list[str])
          - blockers (optional, list[str])
          - estimated_minutes (optional, float, default 30)
          - required_approvals (optional, list[str])
          - expected_outcome (optional, str)
          - severity (optional, str)
        """
        # Sort by priority_score descending
        sorted_proposals = sorted(
            proposals,
            key=lambda p: float(p.get("priority_score", 0)),
            reverse=True,
        )

        actual_id = plan_id or f"plan_{len(proposals)}_{int(datetime.now().timestamp())}"
        now_str = datetime.now().isoformat(timespec="seconds")

        steps: list[PlannedStep] = []
        total_minutes = 0.0
        all_approvals: set[str] = set()
        critical = 0
        blockers = 0

        for i, p in enumerate(sorted_proposals):
            est = float(p.get("estimated_minutes", 30))
            total_minutes += est

            deps = tuple(p.get("depends_on", []))
            blk = tuple(p.get("blockers", []))
            if blk:
                blockers += 1

            approvals = tuple(p.get("required_approvals", []))
            all_approvals.update(approvals)

            sev = str(p.get("severity", "medium"))
            if sev.lower() == "critical":
                critical += 1

            step = PlannedStep(
                proposal_id=p["id"],
                title=str(p.get("title", p["id"])),
                priority_score=float(p.get("priority_score", 0)),
                dependencies=deps,
                blockers=blk,
                estimated_minutes=est,
                required_approvals=approvals,
                expected_outcome=str(p.get("expected_outcome", "")),
                severity=sev,
            )
            steps.append(step)

        return MissionPlan(
            plan_id=actual_id,
            name=name or f"Plan ({len(steps)} steps)",
            steps=tuple(steps),
            total_steps=len(steps),
            total_estimated_minutes=round(total_minutes, 1),
            total_approvals_needed=len(all_approvals),
            critical_count=critical,
            blocker_count=blockers,
            created_at=now_str,
            description=description or f"Mission plan with {len(steps)} steps",
        )
