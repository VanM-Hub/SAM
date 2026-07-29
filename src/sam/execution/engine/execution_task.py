# OP-411 — Execution Task
# Python 3.8, frozen DTO, synchronous, no execute/network/subprocess
# Core DTOs for structured task decomposition of execution plans

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid


@dataclass(frozen=True)
class TaskStatus:
    value: str = "pending"  # pending, validated, scheduled, ready, dispatched, completed, failed, rolled_back

    @staticmethod
    def pending() -> "TaskStatus":
        return TaskStatus("pending")

    @staticmethod
    def validated() -> "TaskStatus":
        return TaskStatus("validated")

    @staticmethod
    def scheduled() -> "TaskStatus":
        return TaskStatus("scheduled")

    @staticmethod
    def ready() -> "TaskStatus":
        return TaskStatus("ready")

    @staticmethod
    def dispatched() -> "TaskStatus":
        return TaskStatus("dispatched")

    @staticmethod
    def completed() -> "TaskStatus":
        return TaskStatus("completed")

    @staticmethod
    def failed() -> "TaskStatus":
        return TaskStatus("failed")

    @staticmethod
    def rolled_back() -> "TaskStatus":
        return TaskStatus("rolled_back")

    def is_terminal(self) -> bool:
        return self.value in ("completed", "failed", "rolled_back")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TaskRisk:
    level: str = "low"
    score: float = 0.0
    factors: Tuple[str, ...] = field(default_factory=tuple)
    description: str = ""


@dataclass(frozen=True)
class TaskCondition:
    condition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # success, failure, always, custom
    expression: str = ""


@dataclass(frozen=True)
class TaskDependency:
    depends_on: str = ""
    condition: str = "success"  # success, failure, always, completion
    required: bool = True


@dataclass(frozen=True)
class TaskMetadata:
    created_by: str = ""
    source: str = ""
    connector_type: str = ""
    action: str = ""
    target_name: str = ""
    tags: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExecutionTask:
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    connector_type: str = ""
    action: str = ""
    target: str = ""
    status: TaskStatus = field(default_factory=TaskStatus.pending)
    risk: TaskRisk = field(default_factory=TaskRisk)
    dependencies: Tuple[TaskDependency, ...] = field(default_factory=tuple)
    conditions: Tuple[TaskCondition, ...] = field(default_factory=tuple)
    metadata: Optional[TaskMetadata] = None
    estimated_duration_seconds: int = 0
    requires_approval: bool = True
    requires_guardian: bool = False
    rollback_task_id: Optional[str] = None
    parallel_group: int = 0
    order: int = 0

    @property
    def is_ready_for_dispatch(self) -> bool:
        return self.status.value in ("ready", "scheduled", "validated")

    def with_status(self, new_status: TaskStatus) -> "ExecutionTask":
        return ExecutionTask(
            task_id=self.task_id, name=self.name,
            description=self.description,
            connector_type=self.connector_type, action=self.action,
            target=self.target, status=new_status,
            risk=self.risk, dependencies=self.dependencies,
            conditions=self.conditions, metadata=self.metadata,
            estimated_duration_seconds=self.estimated_duration_seconds,
            requires_approval=self.requires_approval,
            requires_guardian=self.requires_guardian,
            rollback_task_id=self.rollback_task_id,
            parallel_group=self.parallel_group, order=self.order,
        )


@dataclass(frozen=True)
class TaskGroup:
    group_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tasks: Tuple[ExecutionTask, ...] = field(default_factory=tuple)
    parallel: bool = True
    rollback_group_id: Optional[str] = None
    estimated_duration_seconds: int = 0

    @property
    def total_tasks(self) -> int:
        return len(self.tasks)


@dataclass(frozen=True)
class TaskResult:
    task_id: str = ""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = field(default_factory=TaskStatus.pending)
    success: bool = False
    output: str = ""
    error: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
