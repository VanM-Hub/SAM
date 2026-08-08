# Planning Explainability - WP-18
# IP-3.2-002 (AO-3.2-001 / ED-3.2-002)
#
# Menjelaskan mengapa suatu rencana dihasilkan (evidence-backed).
# Menghasilkan penjelasan deterministik berbasis observasi:
# kondisi komponen, dependensi, readiness, prioritas, dan heuristik yang
# dipakai. Murni deskriptif - menjelaskan alasan, TIDAK mengambil keputusan.
#
# Prinsip: plan with explanation; never decide.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.planning.models import PlanStep, PlanningContext, RuntimePlan
from sam.autonomy_runtime.planning.dependency_planner import DependencyPlanner
from sam.autonomy_runtime.optimization.engine import OptimizationResult


@dataclass(frozen=True)
class PlanningExplanation:
    """Penjelasan deterministik mengapa rencana disusun demikian (immutable)."""

    plan_id: str
    basis: str
    conditions: Tuple[str, ...]  # kondisi observasi yang menjadi alasan
    dependencies: Tuple[str, ...]  # ringkasan dependensi relevan
    priorities: Tuple[str, ...]  # alasan prioritas per step
    heuristics: Tuple[str, ...]  # heuristik yang dipakai
    is_proposal_only: bool = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "basis": self.basis,
            "conditions": list(self.conditions),
            "dependencies": list(self.dependencies),
            "priorities": list(self.priorities),
            "heuristics": list(self.heuristics),
            "is_proposal_only": self.is_proposal_only,
        }


class PlanningExplainer:
    """Menghasilkan penjelasan mengapa rencana dihasilkan (read-only)."""

    def explain_plan(self, plan: RuntimePlan) -> PlanningExplanation:
        ctx = plan.context
        conditions: List[str] = []
        for name in ctx.unavailable_components:
            conditions.append("{} unavailable".format(name))
        for name in ctx.degraded_components:
            conditions.append("{} degraded".format(name))
        for name in ctx.healthy_components:
            conditions.append("{} healthy".format(name))
        if not conditions:
            conditions.append("all observed components healthy/unknown")

        dp = DependencyPlanner(ctx)
        deps: List[str] = []
        for step in plan.steps:
            deps.append(dp.dependency_gate_summary(step.target))

        priorities: List[str] = []
        for step in sorted(plan.steps, key=lambda s: (-s.priority, s.step_id)):
            priorities.append(
                "{} (priority {}) proposed because {}".format(
                    step.action, step.priority, step.reason or "observed condition"
                )
            )

        heuristics = [
            "deterministic priority ordering",
            "dependency-aware sequencing",
            "readiness-aware prioritization",
        ]
        return PlanningExplanation(
            plan_id=plan.plan_id,
            basis=plan.metadata.basis,
            conditions=tuple(conditions),
            dependencies=tuple(deps) if deps else (),
            priorities=tuple(priorities),
            heuristics=tuple(heuristics),
        )

    def explain_optimization(self, opt: OptimizationResult) -> Tuple[str, ...]:
        """Jelaskan perbaikan urutan yang dihasilkan optimasi."""
        lines: List[str] = []
        if not opt.changed:
            lines.append("no reordering needed; original order already optimal")
        lines.extend(opt.improvements)
        return tuple(lines)
