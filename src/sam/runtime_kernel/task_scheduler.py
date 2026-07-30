"""Task Scheduler — penjadwalan task."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_scheduler import TaskSlot


class TaskScheduler:
    """Penjadwal task — preview-only."""

    def __init__(self) -> None:
        self._tasks: Dict[str, TaskSlot] = {}

    def add(self, task: TaskSlot) -> None:
        self._tasks[task.task_id] = task

    def get(self, task_id: str) -> TaskSlot | None:
        return self._tasks.get(task_id)

    def mark_running(self, task_id: str) -> TaskSlot | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        t2 = TaskSlot(task.task_id, task.task_name, task.priority, "running")
        self._tasks[task_id] = t2
        return t2

    def mark_complete(self, task_id: str) -> TaskSlot | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        t2 = TaskSlot(task.task_id, task.task_name, task.priority, "completed")
        self._tasks[task_id] = t2
        return t2

    def list_pending(self) -> List[TaskSlot]:
        return [t for t in self._tasks.values() if t.status == "pending"]

    def count(self) -> int:
        return len(self._tasks)
