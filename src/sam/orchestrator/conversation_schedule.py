# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 128 - Scheduling: conversation_schedule.

Read-only conversation bridge for scheduling.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from .schedule_registry import ScheduleRegistry
from .schedule_plan import SchedulePlan


class ConversationScheduleBridge:
    """Read-only bridge exposing scheduling."""

    def __init__(self, registry: ScheduleRegistry) -> None:
        self._registry = registry

    def locate(self, schedule_id: str) -> Optional[SchedulePlan]:
        return self._registry.get(schedule_id)

    def count(self) -> int:
        return self._registry.count()

    def order_of(self, plan: SchedulePlan) -> Tuple[str, ...]:
        return plan.order

    def summary(self) -> Dict[str, int]:
        return {"schedules": self._registry.count()}
