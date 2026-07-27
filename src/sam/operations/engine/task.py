"""
Task Engine — membaca task dari telemetry dan menyusun task list.
"""

import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ...telemetry.service import TelemetryService
from ...experience.models.task import TaskModel, TaskStatus, TaskStep, TaskApproval
from ...language.mapping import humanize

logger = structlog.get_logger()


class TaskEngine:
    """Engine untuk mengelola task dari telemetry."""

    def __init__(self, telemetry):
        self.telemetry = telemetry

    def get_tasks(self, active_only=False):
        """Get all tasks from telemetry."""
        # Query task-related events
        events = self.telemetry.query({
            "component": ["workflow", "planner", "execution", "operations"],
        })

        # Kelompokkan berdasarkan workflow_id / correlation_id
        task_events = {}
        for e in events:
            key = e.workflow_id or e.correlation_id
            if key:
                if key not in task_events:
                    task_events[key] = []
                task_events[key].append(e)

        # Bangun TaskModel dari event group
        tasks = []
        for task_id, evts in task_events.items():
            task = self._build_task(task_id, evts)
            if task:
                if active_only and not task.is_active:
                    continue
                tasks.append(task)

        # Urutkan: active tasks first, then by created_at (ascending / newest first among same group)
        tasks.sort(
            key=lambda t: (0 if t.is_active else 1, t.created_at),
        )
        return tasks

    def get_task(self, task_id):
        """Get single task by ID."""
        tasks = self.get_tasks()
        for t in tasks:
            if t.id == task_id:
                return t
        return None

    def get_active_tasks(self):
        """Get only active tasks."""
        return self.get_tasks(active_only=True)

    def get_pending_approvals(self):
        """Get tasks that need approval."""
        tasks = self.get_tasks()
        return [t for t in tasks if t.needs_approval]

    def _build_task(self, task_id, events):
        """Build TaskModel from events."""
        if not events:
            return None

        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp)

        first = events[0]
        last = events[-1]

        # Determine status
        status = self._determine_status(events)

        # Build steps
        steps = self._build_steps(events)

        # Build approval
        approval = self._build_approval(events)

        # Progress
        progress = self._calculate_progress(events, steps)

        # Name dari event pertama atau metadata
        name = self._extract_name(events, first)

        return TaskModel(
            id=task_id,
            name=name,
            description=self._extract_description(events),
            status=status,
            progress=progress,
            steps=steps,
            current_step_index=0,
            approval=approval,
            created_at=first.timestamp,
            started_at=self._get_started_at(events),
            completed_at=self._get_completed_at(events),
            estimated_duration_seconds=None,
            owner=None,
            correlation_id=first.correlation_id,
            metadata={"event_count": len(events)}
        )

    def _determine_status(self, events):
        """Determine task status from events."""
        for e in events:
            if "completed" in e.type.value:
                return TaskStatus.COMPLETED
            if "failed" in e.type.value:
                return TaskStatus.FAILED
            if "cancelled" in e.type.value:
                return TaskStatus.CANCELLED
            if "approval" in e.type.value or "approving" in e.type.value:
                return TaskStatus.APPROVING
            if "paused" in e.type.value:
                return TaskStatus.PAUSED
            if "started" in e.type.value:
                return TaskStatus.RUNNING
        return TaskStatus.PENDING

    def _build_steps(self, events):
        """Build steps from events."""
        steps = []
        for i, e in enumerate(events):
            if "progress" in e.type.value or "step" in e.type.value:
                steps.append(TaskStep(
                    id="step_{}".format(i),
                    name=e.message or "Step {}".format(i + 1),
                    status=self._determine_status([e]),
                    started_at=e.timestamp,
                    completed_at=e.timestamp if "completed" in e.type.value else None,
                    logs=[e.message] if e.message else []
                ))
        return steps

    def _build_approval(self, events):
        """Build approval from events."""
        approval_needed = False
        for e in events:
            if "approval" in e.type.value:
                approval_needed = True
                if "approved" in e.type.value:
                    return TaskApproval(
                        required=True,
                        status="approved",
                        approved_at=e.timestamp
                    )
                if "denied" in e.type.value:
                    return TaskApproval(
                        required=True,
                        status="denied",
                        denied_at=e.timestamp
                    )
        if approval_needed:
            return TaskApproval(required=True, status="pending")
        return TaskApproval()

    def _calculate_progress(self, events, steps):
        """Calculate progress percentage."""
        if not steps:
            # Jika tidak ada steps, cari progress events
            for e in events:
                if "progress" in e.type.value and e.metadata and "progress" in e.metadata:
                    return float(e.metadata.get("progress", 0))
            return 0.0

        completed = sum(1 for s in steps if s.status == TaskStatus.COMPLETED)
        return (completed / len(steps)) * 100 if steps else 0

    def _get_started_at(self, events):
        for e in events:
            if "started" in e.type.value:
                return e.timestamp
        return None

    def _get_completed_at(self, events):
        for e in events:
            if "completed" in e.type.value or "finished" in e.type.value:
                return e.timestamp
        return None

    def _extract_name(self, events, first):
        """Extract task name from events."""
        # Coba dari metadata
        if first.metadata and "name" in first.metadata:
            return first.metadata["name"]
        # Dari event message
        if first.message:
            return humanize(first.message[:50])
        return "Task {}".format(first.id[:8])

    def _extract_description(self, events):
        for e in events:
            if e.message and len(e.message) > 20:
                return e.message[:200]
        return None
