"""Runtime Scheduler — DTOs penjadwalan."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ScheduleSlot:
    slot_id: str
    subsystem: str = ""
    priority: int = 0
    allocated: bool = False


@dataclass(frozen=True)
class SchedulePlan:
    plan_id: str
    slots: List[ScheduleSlot] = field(default_factory=list)
    total_slots: int = 0
    allocated_slots: int = 0
    is_full: bool = False


@dataclass(frozen=True)
class ScheduleWindow:
    window_id: str
    start_time: float = 0.0
    end_time: float = 0.0
    subsystem: str = ""


@dataclass(frozen=True)
class TaskSlot:
    task_id: str
    task_name: str = ""
    priority: int = 0
    status: str = "pending"


@dataclass(frozen=True)
class ScheduleResult:
    result_id: str
    scheduled: bool = False
    slot_id: str = ""
