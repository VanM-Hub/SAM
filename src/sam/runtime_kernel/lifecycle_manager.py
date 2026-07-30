"""Lifecycle Manager — mengelola startup/shutdown/restart."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_lifecycle import StartupPlan, ShutdownPlan, RestartPlan, LifecyclePhase


class LifecycleManager:
    """Manager lifecycle — preview-only."""

    def __init__(self) -> None:
        self._startups: Dict[str, StartupPlan] = {}
        self._shutdowns: Dict[str, ShutdownPlan] = {}
        self._restarts: Dict[str, RestartPlan] = {}

    def create_startup(self, plan_id: str, phases: List[LifecyclePhase] = None) -> StartupPlan:
        phases = phases or []
        plan = StartupPlan(
            plan_id=plan_id,
            phases=phases,
            total_phases=len(phases),
            completed_phases=0,
            is_ready=False,
        )
        self._startups[plan_id] = plan
        return plan

    def complete_startup_phase(self, plan_id: str, phase_id: str) -> StartupPlan | None:
        plan = self._startups.get(plan_id)
        if not plan:
            return None
        new_phases = []
        completed = 0
        for p in plan.phases:
            if p.phase_id == phase_id:
                p2 = LifecyclePhase(p.phase_id, p.name, "completed", p.order)
                new_phases.append(p2)
                completed += 1
            else:
                if p.status == "completed":
                    completed += 1
                new_phases.append(p)
        ready = completed == len(new_phases) and len(new_phases) > 0
        p2 = StartupPlan(
            plan_id=plan_id,
            phases=new_phases,
            total_phases=len(new_phases),
            completed_phases=completed,
            is_ready=ready,
        )
        self._startups[plan_id] = p2
        return p2

    def create_shutdown(self, plan_id: str, reason: str = "",
                        graceful: bool = True) -> ShutdownPlan:
        plan = ShutdownPlan(plan_id=plan_id, reason=reason, graceful=graceful)
        self._shutdowns[plan_id] = plan
        return plan

    def mark_shutdown_complete(self, plan_id: str) -> ShutdownPlan | None:
        plan = self._shutdowns.get(plan_id)
        if not plan:
            return None
        p2 = ShutdownPlan(
            plan_id=plan_id,
            reason=plan.reason,
            graceful=plan.graceful,
            total_tasks=1,
            completed_tasks=1,
            is_complete=True,
        )
        self._shutdowns[plan_id] = p2
        return p2

    def create_restart(self, plan_id: str, shutdown_id: str, startup_id: str) -> RestartPlan:
        plan = RestartPlan(plan_id=plan_id, shutdown_id=shutdown_id,
                          startup_id=startup_id, status="pending")
        self._restarts[plan_id] = plan
        return plan

    def complete_restart(self, plan_id: str) -> RestartPlan | None:
        plan = self._restarts.get(plan_id)
        if not plan:
            return None
        p2 = RestartPlan(
            plan_id=plan_id,
            shutdown_id=plan.shutdown_id,
            startup_id=plan.startup_id,
            status="completed",
        )
        self._restarts[plan_id] = p2
        return p2

    def get_startup(self, plan_id: str) -> StartupPlan | None:
        return self._startups.get(plan_id)

    def get_shutdown(self, plan_id: str) -> ShutdownPlan | None:
        return self._shutdowns.get(plan_id)

    def get_restart(self, plan_id: str) -> RestartPlan | None:
        return self._restarts.get(plan_id)

    def count_startups(self) -> int:
        return len(self._startups)

    def count_shutdowns(self) -> int:
        return len(self._shutdowns)

    def count_restarts(self) -> int:
        return len(self._restarts)
