from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class JobType(str, Enum):
    WORKFLOW = "workflow"
    HEALTH_CHECK = "health_check"
    KNOWLEDGE_IMPORT = "knowledge_import"
    PLUGIN_SCAN = "plugin_scan"
    REPORT_GENERATION = "report_generation"
    MIGRATION = "migration"
    CUSTOM = "custom"


class Job(BaseModel):
    """Immutable job definition."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: JobType
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    correlation_id: Optional[str] = None
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    timeout_seconds: Optional[int] = None
    max_attempts: int = 3

    model_config = {"frozen": True}


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobRecord(BaseModel):
    """Job with its current status."""

    job: Job
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    attempts: int = 0
