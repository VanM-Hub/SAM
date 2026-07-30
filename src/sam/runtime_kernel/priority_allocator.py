"""Priority Allocator — alokasi prioritas."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_scheduler import ScheduleSlot, TaskSlot


class PriorityAllocator:
    """Alokator prioritas — preview-only."""

    def allocate_slots(self, slots: List[ScheduleSlot], tasks: List[TaskSlot]) -> List[ScheduleSlot]:
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        result = list(slots)
        for slot in result:
            if not slot.allocated and sorted_tasks:
                task = sorted_tasks.pop(0)
                idx = result.index(slot)
                result[idx] = ScheduleSlot(slot.slot_id, task.task_name,
                                          task.priority, True)
        return result

    def get_highest_priority(self, slots: List[ScheduleSlot]) -> int:
        if not slots:
            return 0
        return max(s.priority for s in slots)
