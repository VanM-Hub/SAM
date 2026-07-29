# OP-421 — Dispatch Request
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid


@dataclass(frozen=True)
class DispatchStatus:
    value: str = "pending"  # pending, validated, approved, queued, dispatched, completed, failed, cancelled

    @staticmethod
    def pending() -> "DispatchStatus":
        return DispatchStatus("pending")

    @staticmethod
    def validated() -> "DispatchStatus":
        return DispatchStatus("validated")

    @staticmethod
    def approved() -> "DispatchStatus":
        return DispatchStatus("approved")

    @staticmethod
    def queued() -> "DispatchStatus":
        return DispatchStatus("queued")

    @staticmethod
    def dispatched() -> "DispatchStatus":
        return DispatchStatus("dispatched")

    @staticmethod
    def completed() -> "DispatchStatus":
        return DispatchStatus("completed")

    @staticmethod
    def failed() -> "DispatchStatus":
        return DispatchStatus("failed")

    @staticmethod
    def cancelled() -> "DispatchStatus":
        return DispatchStatus("cancelled")

    def is_terminal(self) -> bool:
        return self.value in ("completed", "failed", "cancelled")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DispatchPriority:
    value: int = 0  # higher = higher priority

    @staticmethod
    def low() -> "DispatchPriority":
        return DispatchPriority(0)

    @staticmethod
    def normal() -> "DispatchPriority":
        return DispatchPriority(5)

    @staticmethod
    def high() -> "DispatchPriority":
        return DispatchPriority(10)

    @staticmethod
    def critical() -> "DispatchPriority":
        return DispatchPriority(20)


@dataclass(frozen=True)
class DispatchMetadata:
    source: str = ""
    connector_type: str = ""
    action: str = ""
    target: str = ""
    package_id: str = ""
    plan_id: str = ""
    tags: Tuple[str, ...] = field(default_factory=tuple)
    retry_count: int = 0
    max_retries: int = 3


@dataclass(frozen=True)
class DispatchTarget:
    connector_id: str = ""
    connector_type: str = ""
    host: str = ""
    healthy: bool = True


@dataclass(frozen=True)
class DispatchTask:
    task_id: str = ""
    name: str = ""
    action: str = ""
    target: str = ""
    status: DispatchStatus = field(default_factory=DispatchStatus.pending)
    estimated_duration_seconds: int = 0


@dataclass(frozen=True)
class DispatchBatch:
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tasks: Tuple[DispatchTask, ...] = field(default_factory=tuple)
    total_tasks: int = 0
    status: DispatchStatus = field(default_factory=DispatchStatus.pending)


@dataclass(frozen=True)
class DispatchSummary:
    total_dispatch: int = 0
    pending: int = 0
    queued: int = 0
    dispatched: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    estimated_duration_seconds: int = 0


@dataclass(frozen=True)
class DispatchRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    package_id: str = ""
    tasks: Tuple[DispatchTask, ...] = field(default_factory=tuple)
    target: Optional[DispatchTarget] = None
    metadata: Optional[DispatchMetadata] = None
    priority: DispatchPriority = field(default_factory=DispatchPriority.normal)
    status: DispatchStatus = field(default_factory=DispatchStatus.pending)
    requires_approval: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    approved_by: str = ""

    @property
    def total_tasks(self) -> int:
        return len(self.tasks)

    def with_status(self, new_status: DispatchStatus) -> "DispatchRequest":
        return DispatchRequest(
            request_id=self.request_id, package_id=self.package_id,
            tasks=self.tasks, target=self.target, metadata=self.metadata,
            priority=self.priority, status=new_status,
            requires_approval=self.requires_approval,
            created_at=self.created_at, approved_at=self.approved_at,
            approved_by=self.approved_by,
        )
