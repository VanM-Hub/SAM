"""Mission Builder — membangun rencana mission (Sprint 159).

Agent Runtime — builder hanya menyusun urutan runtime (rute pipeline).
Tidak memilih strategi, tidak mengeksekusi, tidak memanggil runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .mission_plan import MissionPlan
from .mission_step import MissionStep
from .mission_route import MissionRoute, PIPELINE_ROUTE


@dataclass(frozen=True)
class PlanResult:
    """Hasil pembangunan plan (immutable)."""
    plan: Optional[MissionPlan] = None
    valid: bool = False
    reason: str = ""


class MissionBuilder:
    """Builder rencana mission. Deterministik, preview-only."""

    def build_default(self, plan_id: str, mission_id: str) -> PlanResult:
        """Bangun plan default dari rute pipeline. Tidak mengeksekusi."""
        if not plan_id or not mission_id:
            return PlanResult(valid=False, reason="plan_id & mission_id required")
        steps = [
            MissionStep(
                step_id=f"{plan_id}.step.{i}",
                plan_id=plan_id,
                order=i,
                runtime_name=runtime,
            )
            for i, runtime in enumerate(PIPELINE_ROUTE)
        ]
        plan = MissionPlan(plan_id=plan_id, mission_id=mission_id, steps=steps)
        return PlanResult(plan=plan, valid=True)

    def build_from_route(self, plan_id: str, mission_id: str, route: MissionRoute) -> PlanResult:
        if not plan_id or not mission_id:
            return PlanResult(valid=False, reason="plan_id & mission_id required")
        steps = [
            MissionStep(
                step_id=f"{plan_id}.step.{i}",
                plan_id=plan_id,
                order=i,
                runtime_name=runtime,
            )
            for i, runtime in enumerate(route.runtimes)
        ]
        plan = MissionPlan(plan_id=plan_id, mission_id=mission_id, steps=steps)
        return PlanResult(plan=plan, valid=True)
