from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    APPROVING = "approving"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStep(BaseModel):
    """Satu step dalam task."""
    id: str
    name: str
    status: TaskStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    logs: List[str] = Field(default_factory=list)


class TaskApproval(BaseModel):
    """Persetujuan yang diperlukan untuk task."""
    required: bool = False
    approvers: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending, approved, denied
    requested_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    denied_at: Optional[datetime] = None


class TaskModel(BaseModel):
    """ViewModel untuk Task."""
    id: str
    name: str
    description: Optional[str] = None
    status: TaskStatus
    priority: int = 0  # 0-10
    progress: float = 0.0  # 0-100

    # Steps
    steps: List[TaskStep] = Field(default_factory=list)
    current_step_index: int = 0

    # Approval
    approval: TaskApproval = Field(default_factory=TaskApproval)

    # Timeline
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration_seconds: Optional[int] = None

    # Metadata
    owner: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True

    @property
    def is_active(self) -> bool:
        return self.status in [TaskStatus.RUNNING, TaskStatus.APPROVING, TaskStatus.PAUSED]

    @property
    def needs_approval(self) -> bool:
        return self.approval.required and self.approval.status == "pending"

    @property
    def progress_text(self) -> str:
        return "{}%".format(int(self.progress))
