from __future__ import annotations

from typing import Optional, List, Dict, Any
import structlog
import uuid

from .job import Job, JobRecord, JobStatus
from .event_bus import EventBus
from .clock import TimeProvider, SystemClock
from .events import JobEnqueued, JobStarted, JobCompleted, JobFailed


class JobQueue:
    """In-memory job queue with status tracking."""

    def __init__(self, event_bus: EventBus, clock: TimeProvider = None):
        self._event_bus = event_bus
        self._clock = clock or SystemClock()
        self._jobs: Dict[str, JobRecord] = {}
        self._logger = structlog.get_logger()
        self._closed = False

    async def enqueue(self, job: Job) -> str:
        """Add a job to the queue."""
        if self._closed:
            raise RuntimeError("Job queue is closed")

        record = JobRecord(job=job, status=JobStatus.PENDING)
        self._jobs[job.id] = record

        await self._event_bus.publish(JobEnqueued(
            id=str(uuid.uuid4()),
            source="job_queue",
            payload={"job_id": job.id, "type": job.type.value, "priority": job.priority},
        ))

        self._logger.info("job_enqueued", job_id=job.id, type=job.type.value)
        return job.id

    async def dequeue(self) -> Optional[JobRecord]:
        """Get the highest-priority pending job."""
        if self._closed:
            return None

        pending = [
            r
            for r in self._jobs.values()
            if r.status == JobStatus.PENDING
            and (r.job.scheduled_at is None or r.job.scheduled_at <= self._clock.now())
        ]

        if not pending:
            return None

        # Sort by priority (higher first), then by created_at (older first)
        pending.sort(key=lambda r: (-r.job.priority, r.job.created_at))
        record = pending[0]

        record.status = JobStatus.RUNNING
        record.started_at = self._clock.now()
        record.attempts += 1

        await self._event_bus.publish(JobStarted(
            id=str(uuid.uuid4()),
            source="job_queue",
            payload={"job_id": record.job.id, "type": record.job.type.value},
        ))

        self._logger.info("job_started", job_id=record.job.id, attempts=record.attempts)
        return record

    async def complete(self, job_id: str, result: Any = None) -> None:
        """Mark a job as completed."""
        record = self._jobs.get(job_id)
        if not record:
            raise ValueError(f"Job not found: {job_id}")

        if record.status != JobStatus.RUNNING:
            raise ValueError(f"Job {job_id} is not running (status: {record.status})")

        record.status = JobStatus.COMPLETED
        record.completed_at = self._clock.now()

        await self._event_bus.publish(JobCompleted(
            id=str(uuid.uuid4()),
            source="job_queue",
            payload={"job_id": job_id, "result": result},
        ))

        self._logger.info("job_completed", job_id=job_id)

    async def fail(self, job_id: str, error: str) -> None:
        """Mark a job as failed."""
        record = self._jobs.get(job_id)
        if not record:
            raise ValueError(f"Job not found: {job_id}")

        record.status = JobStatus.FAILED
        record.completed_at = self._clock.now()
        record.error = error

        await self._event_bus.publish(JobFailed(
            id=str(uuid.uuid4()),
            source="job_queue",
            payload={"job_id": job_id, "error": error},
        ))

        self._logger.warning("job_failed", job_id=job_id, error=error)

    async def cancel(self, job_id: str) -> None:
        """Cancel a pending or running job."""
        record = self._jobs.get(job_id)
        if not record:
            raise ValueError(f"Job not found: {job_id}")

        if record.status not in (JobStatus.PENDING, JobStatus.RUNNING):
            raise ValueError(
                f"Job {job_id} cannot be cancelled (status: {record.status})"
            )

        record.status = JobStatus.CANCELLED
        record.completed_at = self._clock.now()

        self._logger.info("job_cancelled", job_id=job_id)

    async def retry(self, job_id: str) -> None:
        """Reset a failed job to pending (for retry)."""
        record = self._jobs.get(job_id)
        if not record:
            raise ValueError(f"Job not found: {job_id}")

        if record.status != JobStatus.FAILED:
            raise ValueError(f"Job {job_id} cannot be retried (status: {record.status})")

        if record.attempts >= record.job.max_attempts:
            raise ValueError(
                f"Job {job_id} has exceeded max attempts ({record.job.max_attempts})"
            )

        record.status = JobStatus.PENDING
        record.completed_at = None
        record.error = None

        self._logger.info("job_retried", job_id=job_id, attempts=record.attempts)

    async def get_status(self, job_id: str) -> Optional[JobRecord]:
        """Get job status record."""
        return self._jobs.get(job_id)

    async def list_pending(self) -> List[JobRecord]:
        """List all pending jobs."""
        return [r for r in self._jobs.values() if r.status == JobStatus.PENDING]

    async def list_running(self) -> List[JobRecord]:
        """List all running jobs."""
        return [r for r in self._jobs.values() if r.status == JobStatus.RUNNING]

    async def list_all(self) -> List[JobRecord]:
        """List all jobs."""
        return list(self._jobs.values())

    async def close(self) -> None:
        """Close the job queue."""
        self._closed = True
        self._logger.info("job_queue_closed")

    @property
    def closed(self) -> bool:
        return self._closed

    def __len__(self) -> int:
        return len(self._jobs)
