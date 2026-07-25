"""
Persistent Job Queue — SQLite-backed with in-memory cache.

Job Queue menggunakan SQLite agar job survive restart, dengan memory cache
opsional untuk performa query cepat. Semua timestamp menggunakan TimeProvider.
"""

from __future__ import annotations

import json
import uuid
import structlog
from typing import Optional, List, Dict, Any
from datetime import datetime

from .job import Job, JobRecord, JobStatus, JobType
from .event_bus import EventBus
from .clock import TimeProvider, SystemClock
from .events import JobEnqueued, JobStarted, JobCompleted, JobFailed


class JobQueue:
    """Persistent job queue backed by SQLite with optional in-memory cache."""

    def __init__(
        self,
        event_bus: EventBus,
        clock: Optional[TimeProvider] = None,
        db: Optional["Database"] = None,
        use_cache: bool = True,
    ):
        self._event_bus = event_bus
        self._clock = clock or SystemClock()
        self._db = db
        self._logger = structlog.get_logger()
        self._closed = False

        # Optional in-memory cache: job_id -> JobRecord
        self._use_cache = use_cache
        self._cache: Dict[str, JobRecord] = {}

    # ── Private DB helpers ──────────────────────────────────────

    def _has_db(self) -> bool:
        return self._db is not None

    async def _db_execute(self, sql: str, params: Any = None) -> None:
        if self._db:
            # Convert tuple to list for DB.execute compatibility
            db_params = None
            if params is not None:
                if isinstance(params, tuple):
                    db_params = list(params)
                else:
                    db_params = params
            await self._db.execute(sql, db_params)

    async def _db_fetch_one(self, sql: str, params: Any = None) -> Optional[dict]:
        if self._db:
            db_params = None
            if params is not None:
                if isinstance(params, tuple):
                    db_params = list(params)
                else:
                    db_params = params
            return await self._db.fetch_one(sql, db_params)
        return None

    async def _db_fetch_all(self, sql: str, params: Any = None) -> List[dict]:
        if self._db:
            db_params = None
            if params is not None:
                if isinstance(params, tuple):
                    db_params = list(params)
                else:
                    db_params = params
            return await self._db.fetch_all(sql, db_params)
        return []

    def _job_to_db_row(self, job: Job) -> dict:
        return {
            "id": job.id,
            "type": job.type.value,
            "payload": json.dumps(job.payload),
            "priority": job.priority,
            "correlation_id": job.correlation_id,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
            "timeout_seconds": job.timeout_seconds,
            "max_attempts": job.max_attempts,
        }

    def _record_to_db_row(self, record: JobRecord) -> dict:
        return {
            "job_id": record.job.id,
            "status": record.status.value,
            "started_at": record.started_at.isoformat() if record.started_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "error": record.error,
            "attempts": record.attempts,
            "updated_at": (record.started_at or record.job.created_at).isoformat(),
        }

    def _row_to_job(self, row: dict) -> Job:
        """Convert a DB row dict back to a Job model."""
        payload = json.loads(row.get("payload") or "{}")
        return Job(
            id=row["id"],
            type=JobType(row["type"]),
            payload=payload,
            priority=row.get("priority", 0),
            correlation_id=row.get("correlation_id"),
            created_at=datetime.fromisoformat(row["created_at"]),
            scheduled_at=datetime.fromisoformat(row["scheduled_at"]) if row.get("scheduled_at") else None,
            timeout_seconds=row.get("timeout_seconds"),
            max_attempts=row.get("max_attempts", 3),
        )

    def _row_to_record(self, row: dict, job: Optional[Job] = None) -> JobRecord:
        """Convert a DB row dict back to a JobRecord model."""
        if job is None:
            job = self._row_to_job(row)
        return JobRecord(
            job=job,
            status=JobStatus(row.get("status", "pending")),
            started_at=datetime.fromisoformat(row["started_at"]) if row.get("started_at") else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
            error=row.get("error"),
            attempts=row.get("attempts", 0),
        )

    # ── Cache helpers ───────────────────────────────────────────

    def _cache_set(self, record: JobRecord) -> None:
        if self._use_cache:
            self._cache[record.job.id] = record

    def _cache_get(self, job_id: str) -> Optional[JobRecord]:
        if self._use_cache:
            return self._cache.get(job_id)
        return None

    def _cache_remove(self, job_id: str) -> None:
        if self._use_cache:
            self._cache.pop(job_id, None)

    # ── Public API ──────────────────────────────────────────────

    async def enqueue(self, job: Job) -> str:
        """Add a job to the queue."""
        if self._closed:
            raise RuntimeError("Job queue is closed")

        record = JobRecord(job=job, status=JobStatus.PENDING)

        # Persist to DB
        if self._has_db():
            job_row = self._job_to_db_row(job)
            rec_row = self._record_to_db_row(record)
            await self._db_execute(
                """INSERT OR IGNORE INTO jobs
                   (id, type, payload, priority, correlation_id, created_at, scheduled_at, timeout_seconds, max_attempts)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job_row["id"], job_row["type"], job_row["payload"],
                    job_row["priority"], job_row["correlation_id"],
                    job_row["created_at"], job_row["scheduled_at"],
                    job_row["timeout_seconds"], job_row["max_attempts"],
                ),
            )
            await self._db_execute(
                """INSERT OR IGNORE INTO job_records
                   (job_id, status, started_at, completed_at, error, attempts, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    rec_row["job_id"], rec_row["status"],
                    rec_row["started_at"], rec_row["completed_at"],
                    rec_row["error"], rec_row["attempts"], rec_row["updated_at"],
                ),
            )

        # Update cache
        self._cache_set(record)

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

        now = self._clock.now()

        if self._has_db():
            # Atomic: find highest-priority pending job and update to RUNNING
            row = await self._db_fetch_one(
                """SELECT j.*, r.status, r.started_at, r.completed_at, r.error, r.attempts, r.updated_at
                   FROM jobs j
                   JOIN job_records r ON r.job_id = j.id
                   WHERE r.status = ? AND (j.scheduled_at IS NULL OR j.scheduled_at <= ?)
                   ORDER BY j.priority DESC, j.created_at ASC
                   LIMIT 1""",
                (JobStatus.PENDING.value, now.isoformat()),
            )

            if not row:
                return None

            job = self._row_to_job(row)
            record = self._row_to_record(row, job)
        else:
            # In-memory fallback
            pending = [
                r for r in self._cache.values()
                if r.status == JobStatus.PENDING
                and (r.job.scheduled_at is None or r.job.scheduled_at <= now)
            ]
            if not pending:
                return None
            pending.sort(key=lambda r: (-r.job.priority, r.job.created_at))
            record = pending[0]

        record.status = JobStatus.RUNNING
        record.started_at = now
        record.attempts += 1

        # Persist DB update
        if self._has_db():
            await self._db_execute(
                """UPDATE job_records
                   SET status = ?, started_at = ?, attempts = ?, updated_at = ?
                   WHERE job_id = ?""",
                (JobStatus.RUNNING.value, now.isoformat(), record.attempts,
                 now.isoformat(), record.job.id),
            )

        # Update cache
        self._cache_set(record)

        await self._event_bus.publish(JobStarted(
            id=str(uuid.uuid4()),
            source="job_queue",
            payload={"job_id": record.job.id, "type": record.job.type.value},
        ))

        self._logger.info("job_started", job_id=record.job.id, attempts=record.attempts)
        return record

    async def complete(self, job_id: str, result: Any = None) -> None:
        """Mark a job as completed."""
        record = await self._get_record(job_id)
        if not record:
            raise ValueError(f"Job not found: {job_id}")

        if record.status != JobStatus.RUNNING:
            raise ValueError(f"Job {job_id} is not running (status: {record.status})")

        record.status = JobStatus.COMPLETED
        record.completed_at = self._clock.now()

        # Persist DB
        if self._has_db():
            await self._db_execute(
                """UPDATE job_records
                   SET status = ?, completed_at = ?, updated_at = ?
                   WHERE job_id = ?""",
                (JobStatus.COMPLETED.value, record.completed_at.isoformat(),
                 record.completed_at.isoformat(), job_id),
            )

        # Update cache
        self._cache_set(record)

        await self._event_bus.publish(JobCompleted(
            id=str(uuid.uuid4()),
            source="job_queue",
            payload={"job_id": job_id, "result": result},
        ))

        self._logger.info("job_completed", job_id=job_id)

    async def fail(self, job_id: str, error: str) -> None:
        """Mark a job as failed."""
        record = await self._get_record(job_id)
        if not record:
            raise ValueError(f"Job not found: {job_id}")

        record.status = JobStatus.FAILED
        record.completed_at = self._clock.now()
        record.error = error

        # Persist DB
        if self._has_db():
            await self._db_execute(
                """UPDATE job_records
                   SET status = ?, completed_at = ?, error = ?, updated_at = ?
                   WHERE job_id = ?""",
                (JobStatus.FAILED.value, record.completed_at.isoformat(), error,
                 record.completed_at.isoformat(), job_id),
            )

        # Update cache
        self._cache_set(record)

        await self._event_bus.publish(JobFailed(
            id=str(uuid.uuid4()),
            source="job_queue",
            payload={"job_id": job_id, "error": error},
        ))

        self._logger.warning("job_failed", job_id=job_id, error=error)

    async def cancel(self, job_id: str) -> None:
        """Cancel a pending or running job."""
        record = await self._get_record(job_id)
        if not record:
            raise ValueError(f"Job not found: {job_id}")

        if record.status not in (JobStatus.PENDING, JobStatus.RUNNING):
            raise ValueError(
                f"Job {job_id} cannot be cancelled (status: {record.status})"
            )

        record.status = JobStatus.CANCELLED
        record.completed_at = self._clock.now()

        # Persist DB
        if self._has_db():
            await self._db_execute(
                """UPDATE job_records
                   SET status = ?, completed_at = ?, updated_at = ?
                   WHERE job_id = ?""",
                (JobStatus.CANCELLED.value, record.completed_at.isoformat(),
                 record.completed_at.isoformat(), job_id),
            )

        # Update cache
        self._cache_set(record)

        self._logger.info("job_cancelled", job_id=job_id)

    async def retry(self, job_id: str) -> None:
        """Reset a failed job to pending (for retry)."""
        record = await self._get_record(job_id)
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

        # Persist DB
        if self._has_db():
            await self._db_execute(
                """UPDATE job_records
                   SET status = ?, completed_at = ?, error = ?, updated_at = ?
                   WHERE job_id = ?""",
                (JobStatus.PENDING.value, None, None, self._clock.now().isoformat(), job_id),
            )

        # Update cache
        self._cache_set(record)

        self._logger.info("job_retried", job_id=job_id, attempts=record.attempts)

    async def get_status(self, job_id: str) -> Optional[JobRecord]:
        """Get job status record."""
        # Try cache first
        cached = self._cache_get(job_id)
        if cached is not None:
            return cached

        # Fallback to DB
        if self._has_db():
            row = await self._db_fetch_one(
                """SELECT j.*, r.status, r.started_at, r.completed_at, r.error, r.attempts, r.updated_at
                   FROM jobs j
                   JOIN job_records r ON r.job_id = j.id
                   WHERE j.id = ?""",
                (job_id,),
            )
            if row:
                job = self._row_to_job(row)
                record = self._row_to_record(row, job)
                self._cache_set(record)
                return record

        return None

    async def list_pending(self) -> List[JobRecord]:
        """List all pending jobs."""
        if self._has_db():
            rows = await self._db_fetch_all(
                """SELECT j.*, r.status, r.started_at, r.completed_at, r.error, r.attempts, r.updated_at
                   FROM jobs j
                   JOIN job_records r ON r.job_id = j.id
                   WHERE r.status = ?
                   ORDER BY j.priority DESC, j.created_at ASC""",
                (JobStatus.PENDING.value,),
            )
            results = []
            for row in rows:
                job = self._row_to_job(row)
                record = self._row_to_record(row, job)
                self._cache_set(record)
                results.append(record)
            return results

        return [r for r in self._cache.values() if r.status == JobStatus.PENDING]

    async def list_running(self) -> List[JobRecord]:
        """List all running jobs."""
        if self._has_db():
            rows = await self._db_fetch_all(
                """SELECT j.*, r.status, r.started_at, r.completed_at, r.error, r.attempts, r.updated_at
                   FROM jobs j
                   JOIN job_records r ON r.job_id = j.id
                   WHERE r.status = ?""",
                (JobStatus.RUNNING.value,),
            )
            results = []
            for row in rows:
                job = self._row_to_job(row)
                record = self._row_to_record(row, job)
                self._cache_set(record)
                results.append(record)
            return results

        return [r for r in self._cache.values() if r.status == JobStatus.RUNNING]

    async def list_all(self) -> List[JobRecord]:
        """List all jobs."""
        if self._has_db():
            rows = await self._db_fetch_all(
                """SELECT j.*, r.status, r.started_at, r.completed_at, r.error, r.attempts, r.updated_at
                   FROM jobs j
                   JOIN job_records r ON r.job_id = j.id
                   ORDER BY j.created_at DESC""",
            )
            results = []
            for row in rows:
                job = self._row_to_job(row)
                record = self._row_to_record(row, job)
                self._cache_set(record)
                results.append(record)
            return results

        return list(self._cache.values())

    async def stats(self) -> Dict[str, int]:
        """Get queue statistics (counts by status)."""
        if self._has_db():
            rows = await self._db_fetch_all(
                """SELECT status, COUNT(*) as count FROM job_records GROUP BY status""",
            )
            stats = {"total": 0}
            for row in rows:
                stats[row["status"]] = row["count"]
                stats["total"] += row["count"]
            return stats

        # In-memory fallback
        stats = {"total": len(self._cache)}
        statuses = {}
        for r in self._cache.values():
            s = r.status.value
            statuses[s] = statuses.get(s, 0) + 1
        stats.update(statuses)
        return stats

    async def close(self) -> None:
        """Close the job queue."""
        self._closed = True
        self._cache.clear()
        self._logger.info("job_queue_closed")

    async def recover(self) -> int:
        """Recover jobs that were RUNNING on last shutdown — reset them to PENDING.

        Returns the number of recovered jobs.
        """
        if not self._has_db():
            # For in-memory mode, just clean up RUNNING records in cache
            count = 0
            for record in list(self._cache.values()):
                if record.status == JobStatus.RUNNING:
                    record.status = JobStatus.PENDING
                    record.started_at = None
                    count += 1
            if count:
                self._logger.info("job_queue_recovered_in_memory", count=count)
            return count

        # DB mode: reset RUNNING jobs to PENDING
        await self._db_execute(
            """UPDATE job_records
               SET status = ?, started_at = NULL, updated_at = ?
               WHERE status = ?""",
            (JobStatus.PENDING.value, self._clock.now().isoformat(), JobStatus.RUNNING.value),
        )

        # Refresh cache
        self._cache.clear()
        count = 0
        rows = await self._db_fetch_all(
            """SELECT j.*, r.status, r.started_at, r.completed_at, r.error, r.attempts, r.updated_at
               FROM jobs j
               JOIN job_records r ON r.job_id = j.id""",
        )
        for row in rows:
            job = self._row_to_job(row)
            record = self._row_to_record(row, job)
            self._cache_set(record)

        self._logger.info("job_queue_recovered", count=count)
        return count

    @property
    def closed(self) -> bool:
        return self._closed

    def __len__(self) -> int:
        if self._use_cache:
            return len(self._cache)
        return 0

    # ── Internal helpers ────────────────────────────────────────

    async def _get_record(self, job_id: str) -> Optional[JobRecord]:
        """Get a JobRecord from cache or DB."""
        # Cache first
        cached = self._cache_get(job_id)
        if cached is not None:
            return cached

        # DB fallback
        if self._has_db():
            row = await self._db_fetch_one(
                """SELECT j.*, r.status, r.started_at, r.completed_at, r.error, r.attempts, r.updated_at
                   FROM jobs j
                   JOIN job_records r ON r.job_id = j.id
                   WHERE j.id = ?""",
                (job_id,),
            )
            if row:
                job = self._row_to_job(row)
                record = self._row_to_record(row, job)
                self._cache_set(record)
                return record

        return None
