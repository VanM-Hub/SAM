# Planning API - WP-17
# IP-3.2-002 (AO-3.2-001 / ED-3.2-002)
#
# Read-only facade: plan(), schedule(), optimize().
# Menyajikan kemampuan perencanaan runtime melalui satu pintu - semua
# operasi TANPA mengubah runtime, TANPA aksi, TANPA keputusan konstitusional.
# Semua keluaran adalah proposal deterministik.
#
# Prinsip: plan, never decide.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.planning.models import PlanStep, PlanningContext, RuntimePlan
from sam.autonomy_runtime.planning.engine import PlanningEngine
from sam.autonomy_runtime.planning.dependency_planner import DependencyPlanner
from sam.autonomy_runtime.planning.readiness_planner import ReadinessBasedPlanner
from sam.autonomy_runtime.scheduling.engine import SchedulingEngine, SchedulingProposal
from sam.autonomy_runtime.optimization.engine import OptimizationResult, PlanningOptimizer


@dataclass(frozen=True)
class PlanningSummary:
    """Ringkasan agregat hasil perencanaan (immutable, read-only view)."""

    plan_id: str
    step_count: int
    plan_state: str
    schedule_status: str
    ready_steps: int
    blocked_steps: int
    optimized: bool
    plan_ordered_ids: Tuple[str, ...]
    optimized_ordered_ids: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "step_count": self.step_count,
            "plan_state": self.plan_state,
            "schedule_status": self.schedule_status,
            "ready_steps": self.ready_steps,
            "blocked_steps": self.blocked_steps,
            "optimized": self.optimized,
            "plan_ordered_ids": list(self.plan_ordered_ids),
            "optimized_ordered_ids": list(self.optimized_ordered_ids),
        }


class PlanningAPI:
    """Fasad read-only untuk perencanaan runtime (plan/schedule/optimize)."""

    def __init__(
        self,
        engine: Optional[PlanningEngine] = None,
        scheduler: Optional[SchedulingEngine] = None,
        optimizer: Optional[PlanningOptimizer] = None,
    ) -> None:
        self._engine = engine or PlanningEngine()
        self._scheduler = scheduler or SchedulingEngine()
        self._optimizer = optimizer

    # --- plan ---

    def plan(
        self,
        context: PlanningContext,
        available: Optional[Tuple[str, ...]] = None,
        created_at: str = "",
    ) -> RuntimePlan:
        """Bangun rencana operasional dari context (proposal, read-only)."""
        return self._engine.build_plan(context, created_at=created_at)

    # --- schedule ---

    def schedule(
        self,
        plan: RuntimePlan,
        available: Optional[Tuple[str, ...]] = None,
    ) -> SchedulingProposal:
        """Susun jadwal kandidat dari rencana (proposal only)."""
        return self._scheduler.build_schedule(plan, available=available)

    # --- optimize ---

    def optimize(
        self,
        context: PlanningContext,
        steps: Tuple[PlanStep, ...],
        plan_id: str = "",
    ) -> OptimizationResult:
        """Optimalkan urutan step dengan heuristik deterministik."""
        if self._optimizer is None:
            self._optimizer = PlanningOptimizer(context)
        return self._optimizer.optimize(steps, plan_id=plan_id)

    # --- summary / convenience ---

    def full_pipeline(
        self,
        context: PlanningContext,
        available: Optional[Tuple[str, ...]] = None,
        created_at: str = "",
    ) -> Tuple[RuntimePlan, SchedulingProposal, OptimizationResult]:
        """Jalankan plan -> schedule -> optimize sekaligus (read-only)."""
        plan = self.plan(context, available=available, created_at=created_at)
        schedule = self.schedule(plan, available=available)
        opt = self.optimize(context, plan.steps, plan_id=plan.plan_id)
        return plan, schedule, opt

    def summarize(
        self,
        plan: RuntimePlan,
        schedule: SchedulingProposal,
        optimization: Optional[OptimizationResult] = None,
    ) -> PlanningSummary:
        """Ringkasan agregat untuk observasi / integrasi."""
        opt_ids = plan.step_ids()
        optimized = False
        if optimization is not None:
            opt_ids = list(optimization.optimized_order)
            optimized = optimization.changed
        return PlanningSummary(
            plan_id=plan.plan_id,
            step_count=plan.step_count(),
            plan_state=plan.state,
            schedule_status=schedule.status,
            ready_steps=schedule.total_ready,
            blocked_steps=schedule.total_blocked,
            optimized=optimized,
            plan_ordered_ids=plan.step_ids(),
            optimized_ordered_ids=tuple(opt_ids),
        )

    def describe_dependencies(self, context: PlanningContext, target: str) -> Dict[str, Any]:
        """Jelaskan dependensi target (read-only, untuk observasi)."""
        dp = DependencyPlanner(context)
        return {
            "target": target,
            "direct": dp.dependencies_of(target),
            "dependents": dp.dependents_of(target),
            "transitive": sorted(dp.transitive_dependencies(target)),
            "blocking_unavailable": dp.unavailable_dependencies(),
        }
