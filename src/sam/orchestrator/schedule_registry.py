# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 128 - Scheduling: schedule_registry.

Registry that stores schedule plans. Sync, in-memory.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .schedule_request import ScheduleRequest
from .schedule_plan import SchedulePlan


@dataclass(frozen=True)
class ScheduleRegistrationResult:
    schedule_id: str
    accepted: bool
    reason: str = ""


class ScheduleRegistry:
    """Stores schedule plans by id."""

    def __init__(self) -> None:
        self._plans: Dict[str, SchedulePlan] = {}

    def register(
        self, request: ScheduleRequest, order: Tuple[str, ...]
    ) -> ScheduleRegistrationResult:
        plan = SchedulePlan(schedule_id=request.schedule_id, order=order)
        self._plans[request.schedule_id] = plan
        return ScheduleRegistrationResult(
            schedule_id=request.schedule_id, accepted=True, reason="registered"
        )

    def get(self, schedule_id: str) -> Optional[SchedulePlan]:
        return self._plans.get(schedule_id)

    def all(self) -> Tuple[SchedulePlan, ...]:
        return tuple(self._plans.values())

    def count(self) -> int:
        return len(self._plans)
