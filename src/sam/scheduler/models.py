"""Scheduler models for workflow scheduling."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class ScheduleType(str, Enum):
    """Type of schedule."""
    ONCE = "once"           # Run once at a specific time
    INTERVAL = "interval"   # Run every N seconds
    CRON = "cron"           # Run on cron expression


class ScheduleStatus(str, Enum):
    """Status of a schedule."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


class Schedule(BaseModel):
    """Schedule definition for recurring workflow execution."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    workflow_file: str
    schedule_type: ScheduleType = ScheduleType.ONCE
    cron_expression: Optional[str] = None
    delay_seconds: Optional[int] = None
    max_retries: int = 3
    retry_delay: int = 60
    enabled: bool = True
    status: ScheduleStatus = ScheduleStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    run_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def compute_next_run(self) -> Optional[datetime]:
        """Compute the next run time based on schedule type."""
        now = datetime.utcnow()

        if self.schedule_type == ScheduleType.ONCE:
            # For 'once', run at next_run if set, otherwise now
            return self.next_run or now

        elif self.schedule_type == ScheduleType.INTERVAL:
            if self.delay_seconds is None:
                return None
            if self.last_run is None:
                return now
            from datetime import timedelta
            return self.last_run + timedelta(seconds=self.delay_seconds)

        elif self.schedule_type == ScheduleType.CRON:
            if not self.cron_expression:
                return None
            # Use croniter if available, otherwise simple approximation
            try:
                from croniter import croniter
                cron = croniter(self.cron_expression, now)
                return cron.get_next(datetime)
            except ImportError:
                # Fallback: just return now + 1 hour as approximation
                from datetime import timedelta
                return now + timedelta(hours=1)

        return None

    def update_run(self, success: bool = True, error: Optional[str] = None) -> None:
        """Update schedule after a run."""
        now = datetime.utcnow()
        self.last_run = now
        self.updated_at = now
        self.run_count += 1

        if success:
            self.status = ScheduleStatus.PENDING if self.schedule_type != ScheduleType.ONCE else ScheduleStatus.COMPLETED
            self.last_error = None
        else:
            self.last_error = error
            if self.run_count >= self.max_retries:
                self.status = ScheduleStatus.FAILED
            else:
                self.status = ScheduleStatus.PENDING

        self.next_run = self.compute_next_run()


class ScheduleCreate(BaseModel):
    """Input model for creating a schedule."""

    model_config = ConfigDict(extra="forbid")

    name: str
    workflow_file: str
    schedule_type: ScheduleType = ScheduleType.ONCE
    cron_expression: Optional[str] = None
    delay_seconds: Optional[int] = None
    max_retries: int = 3
    retry_delay: int = 60
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)