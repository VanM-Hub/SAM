"""Conversation Scheduler Bridge — 8 queries."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.scheduler_engine import SchedulerEngine
from sam.runtime_kernel.task_scheduler import TaskScheduler
from sam.runtime_kernel.window_scheduler import WindowScheduler
from sam.runtime_kernel.priority_allocator import PriorityAllocator


class ConversationScheduler:
    def __init__(self, engine: SchedulerEngine, tasks: TaskScheduler,
                 windows: WindowScheduler, allocator: PriorityAllocator) -> None:
        self._engine = engine
        self._tasks = tasks
        self._windows = windows
        self._allocator = allocator

    def get_engine(self) -> SchedulerEngine:
        return self._engine

    def get_task_scheduler(self) -> TaskScheduler:
        return self._tasks

    def get_window_scheduler(self) -> WindowScheduler:
        return self._windows

    def get_priority_allocator(self) -> PriorityAllocator:
        return self._allocator

    def describe_layers(self) -> List[str]:
        return ["engine", "tasks", "windows", "allocator"]

    def count_layers(self) -> int:
        return 4

    def get_plan_count(self) -> int:
        return self._engine.count()

    def get_task_count(self) -> int:
        return self._tasks.count()


class DashboardScheduler:
    def __init__(self, engine: SchedulerEngine, tasks: TaskScheduler) -> None:
        self._engine = engine
        self._tasks = tasks

    def engine_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Scheduler Engine",
            description=f"{self._engine.count()} plans",
            status="ready",
            metrics={"plans": self._engine.count(),
                     "tasks": self._tasks.count()},
            items=["plans", "slots"],
        )

    def plan_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Schedule Plans",
            description="Penjadwalan",
            status="ready",
            metrics={"plans": self._engine.count()},
            items=["plans"],
        )

    def task_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Task Scheduler",
            description=f"{self._tasks.count()} tasks",
            status="ready",
            metrics={"tasks": self._tasks.count(),
                     "pending": len(self._tasks.list_pending())},
            items=["tasks"],
        )

    def window_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Window Scheduler",
            description="Schedule windows",
            status="ready",
            metrics={"windows": 0},
            items=["windows"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Scheduler Summary",
            description="Ringkasan penjadwalan",
            status="ready",
            metrics={"layers": 4, "plans": self._engine.count()},
            items=["engine", "tasks", "windows", "allocator"],
        )
