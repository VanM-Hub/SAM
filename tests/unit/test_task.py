"""
Unit tests for Task system (OP-5).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime, timedelta
import pytest
from sam.experience.models.task import TaskModel, TaskStatus, TaskStep, TaskApproval
from sam.operations.engine.task import TaskEngine
from sam.telemetry import (
    TelemetryEvent, TelemetryEventType, EventSeverity,
    EventCategory, Component, TelemetryService,
)


# ============================================================================
# 1. TaskStatus Enum
# ============================================================================

class TestTaskStatus:
    def test_all_statuses_exist(self):
        """All 7 task statuses exist."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.APPROVING.value == "approving"
        assert TaskStatus.PAUSED.value == "paused"

    def test_seven_statuses(self):
        """Exactly 7 statuses."""
        assert len(list(TaskStatus)) == 7


# ============================================================================
# 2. TaskStep
# ============================================================================

class TestTaskStep:
    def test_minimal_step(self):
        """Can create TaskStep with minimum fields."""
        step = TaskStep(id="s1", name="Step 1", status=TaskStatus.PENDING)
        assert step.id == "s1"
        assert step.logs == []

    def test_full_step(self):
        """Can create TaskStep with all fields."""
        now = datetime.utcnow()
        step = TaskStep(
            id="s2", name="Step 2", status=TaskStatus.COMPLETED,
            started_at=now, completed_at=now + timedelta(seconds=5),
            duration_ms=5000.0, logs=["started", "completed"],
        )
        assert step.duration_ms == 5000.0
        assert len(step.logs) == 2


# ============================================================================
# 3. TaskApproval
# ============================================================================

class TestTaskApproval:
    def test_default_approval(self):
        """Default approval not required."""
        a = TaskApproval()
        assert a.required is False
        assert a.status == "pending"

    def test_approved_approval(self):
        """Approved approval."""
        now = datetime.utcnow()
        a = TaskApproval(required=True, status="approved", approved_at=now)
        assert a.required is True
        assert a.status == "approved"
        assert a.approved_at == now


# ============================================================================
# 4. TaskModel
# ============================================================================

class TestTaskModel:
    def test_minimal_task(self):
        """Can create TaskModel with minimum fields."""
        now = datetime.utcnow()
        task = TaskModel(
            id="t1", name="Test Task", status=TaskStatus.PENDING,
            created_at=now,
        )
        assert task.id == "t1"
        assert task.progress == 0.0
        assert task.steps == []

    def test_task_is_frozen(self):
        """TaskModel is immutable."""
        now = datetime.utcnow()
        task = TaskModel(id="t1", name="Test", status=TaskStatus.PENDING, created_at=now)
        with pytest.raises((TypeError, Exception)):
            task.name = "Changed"

    def test_is_active_property(self):
        """is_active returns True for running/approving/paused."""
        now = datetime.utcnow()
        running = TaskModel(id="t1", name="R", status=TaskStatus.RUNNING, created_at=now)
        pending = TaskModel(id="t2", name="P", status=TaskStatus.PENDING, created_at=now)
        assert running.is_active is True
        assert pending.is_active is False

    def test_needs_approval_property(self):
        """needs_approval returns True when approval pending."""
        now = datetime.utcnow()
        needs = TaskModel(
            id="t1", name="Approval needed", status=TaskStatus.APPROVING,
            created_at=now,
            approval=TaskApproval(required=True, status="pending"),
        )
        no_need = TaskModel(id="t2", name="No", status=TaskStatus.PENDING, created_at=now)
        assert needs.needs_approval is True
        assert no_need.needs_approval is False

    def test_progress_text(self):
        """progress_text returns formatted string."""
        now = datetime.utcnow()
        task = TaskModel(id="t1", name="T", status=TaskStatus.RUNNING,
                         created_at=now, progress=75.0)
        assert task.progress_text == "75%"


# ============================================================================
# 5. TaskEngine
# ============================================================================

class TestTaskEngine:
    def test_empty_telemetry_returns_empty(self):
        """No events means no tasks."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = TaskEngine(svc)
        tasks = engine.get_tasks()
        assert tasks == []

    def test_task_from_workflow_events(self):
        """Events with workflow_id become a task."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_STARTED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Repair started",
            workflow_id="wf-001",
        ))
        engine = TaskEngine(svc)
        tasks = engine.get_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == "wf-001"

    def test_task_status_completed(self):
        """Task with completed event has COMPLETED status."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_COMPLETED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Repair completed",
            workflow_id="wf-002",
        ))
        engine = TaskEngine(svc)
        tasks = engine.get_tasks()
        assert tasks[0].status == TaskStatus.COMPLETED

    def test_task_status_failed(self):
        """Task with failed event has FAILED status."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_FAILED,
            component=Component.WORKFLOW,
            severity=EventSeverity.ERROR,
            category=EventCategory.EXECUTION,
            message="Repair failed",
            workflow_id="wf-003",
        ))
        engine = TaskEngine(svc)
        tasks = engine.get_tasks()
        assert tasks[0].status == TaskStatus.FAILED

    def test_active_tasks_filter(self):
        """get_active_tasks returns only active tasks."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        now = datetime.utcnow()
        # Active
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_STARTED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Active task",
            workflow_id="wf-active",
        ))
        # Completed
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_COMPLETED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Done task",
            workflow_id="wf-done",
        ))
        engine = TaskEngine(svc)
        active = engine.get_active_tasks()
        assert len(active) == 1
        assert active[0].id == "wf-active"

    def test_pending_approvals(self):
        """get_pending_approvals returns tasks needing approval."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.OPERATOR_APPROVAL,
            component=Component.OPERATIONS,
            category=EventCategory.APPROVAL,
            message="Approval required",
            workflow_id="wf-approve",
        ))
        engine = TaskEngine(svc)
        pending = engine.get_pending_approvals()
        assert len(pending) == 1

    def test_get_task_by_id(self):
        """get_task returns specific task."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_STARTED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Task",
            workflow_id="wf-find",
        ))
        engine = TaskEngine(svc)
        task = engine.get_task("wf-find")
        assert task is not None
        assert task.id == "wf-find"
        assert engine.get_task("nonexistent") is None

    def test_task_with_steps(self):
        """Progress events become task steps."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        now = datetime.utcnow()
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_STARTED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Task started",
            workflow_id="wf-steps",
            timestamp=now,
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_PROGRESS,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Step 1",
            workflow_id="wf-steps",
            timestamp=now + timedelta(seconds=1),
        ))
        engine = TaskEngine(svc)
        tasks = engine.get_tasks()
        assert len(tasks) == 1
        assert len(tasks[0].steps) >= 1

    def test_correlation_id_as_task_id(self):
        """Events with correlation_id (no workflow_id) become a task."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_STARTED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Task",
            correlation_id="corr-task",
        ))
        engine = TaskEngine(svc)
        tasks = engine.get_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == "corr-task"

    def test_active_tasks_sorted_first(self):
        """Active tasks appear before completed ones."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        # Completed first (older)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_COMPLETED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Old completed",
            workflow_id="wf-old",
            timestamp=datetime.utcnow() - timedelta(hours=1),
        ))
        # Active newer
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_STARTED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Active newer",
            workflow_id="wf-active",
            timestamp=datetime.utcnow(),
        ))
        engine = TaskEngine(svc)
        tasks = engine.get_tasks()
        # Get first active task
        active_tasks = [t for t in tasks if t.is_active]
        inactive_tasks = [t for t in tasks if not t.is_active]
        assert len(active_tasks) == 1
        assert len(inactive_tasks) == 1
        # Active comes before inactive in the list
        active_idx = next(i for i, t in enumerate(tasks) if t.is_active)
        inactive_idx = next(i for i, t in enumerate(tasks) if not t.is_active)
        assert active_idx < inactive_idx
