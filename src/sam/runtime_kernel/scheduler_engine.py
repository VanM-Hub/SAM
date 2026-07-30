"""Scheduler Engine — engine penjadwalan."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_scheduler import ScheduleSlot, SchedulePlan, ScheduleResult


class SchedulerEngine:
    """Engine penjadwalan — preview-only."""

    def __init__(self) -> None:
        self._plans: Dict[str, SchedulePlan] = {}

    def create_plan(self, plan_id: str, slots: List[ScheduleSlot] = None) -> SchedulePlan:
        slots = slots or []
        allocated = sum(1 for s in slots if s.allocated)
        plan = SchedulePlan(
            plan_id=plan_id,
            slots=slots,
            total_slots=len(slots),
            allocated_slots=allocated,
            is_full=allocated == len(slots) if slots else False,
        )
        self._plans[plan_id] = plan
        return plan

    def allocate(self, plan_id: str, slot_id: str) -> ScheduleResult:
        plan = self._plans.get(plan_id)
        if not plan:
            return ScheduleResult(f"{plan_id}/{slot_id}", False, "")
        new_slots = []
        found = False
        for s in plan.slots:
            if s.slot_id == slot_id:
                s2 = ScheduleSlot(s.slot_id, s.subsystem, s.priority, True)
                new_slots.append(s2)
                found = True
            else:
                new_slots.append(s)
        if not found:
            return ScheduleResult(f"{plan_id}/{slot_id}", False, "")
        allocated = sum(1 for s in new_slots if s.allocated)
        p2 = SchedulePlan(
            plan_id=plan_id,
            slots=new_slots,
            total_slots=plan.total_slots,
            allocated_slots=allocated,
            is_full=allocated == plan.total_slots,
        )
        self._plans[plan_id] = p2
        return ScheduleResult(f"{plan_id}/{slot_id}", True, slot_id)

    def get_plan(self, plan_id: str) -> SchedulePlan | None:
        return self._plans.get(plan_id)

    def count(self) -> int:
        return len(self._plans)
