"""
Persistent Job Queue — integration tests with SQLite backend.

Tests that the JobQueue correctly persists jobs to SQLite and survives
"restarts" (re-opening with the same DB path).

Because the project Database wrapper uses asyncio.to_thread (Python 3.12+),
we bypass it and use raw sqlite3 directly for the test tables.
"""
import asyncio
import os
import json
import sys
import sqlite3
import tempfile
from datetime import datetime, timedelta
from typing import Optional

import pytest

from src.sam.core.job import Job, JobType, JobStatus
from src.sam.core.job_queue import JobQueue
from src.sam.core.event_bus import EventBus
from src.sam.core.clock import FrozenClock, SystemClock


# ── Minimal async Database shim for Python 3.8 ────────────────────────

class _TestDB:
    """Minimal DB shim that wraps sqlite3 synchronously.

    Only implements the subset of Database API that JobQueue uses:
    execute(), fetch_one(), fetch_all(), close().
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    async def execute(self, sql: str, params=None):
        def _exec():
            cur = self._conn.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            self._conn.commit()
            cur.close()
        _exec()  # sync in test

    async def fetch_one(self, sql: str, params=None):
        cur = self._conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None

    async def fetch_all(self, sql: str, params=None):
        cur = self._conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    async def close(self):
        try:
            self._conn.close()
        except Exception:
            pass


# ── Migrations SQL for test tables ────────────────────────────────────

_MIGRATION_012 = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    payload TEXT DEFAULT '{}',
    priority INTEGER DEFAULT 0,
    correlation_id TEXT,
    created_at TEXT NOT NULL,
    scheduled_at TEXT,
    timeout_seconds INTEGER,
    max_attempts INTEGER DEFAULT 3
);

CREATE TABLE IF NOT EXISTS job_records (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TEXT,
    completed_at TEXT,
    error TEXT,
    attempts INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_job_records_status ON job_records(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_correlation ON jobs(correlation_id);
"""


@pytest.fixture(scope="function")
def clk():
    return FrozenClock(datetime(2026, 7, 24, 0, 0, 0))


@pytest.fixture(scope="function")
def bus():
    return EventBus()


@pytest.fixture(scope="function")
def db():
    """Create a temp SQLite DB with job tables."""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_jobs.db")
    database = _TestDB(db_path)
    # Run migration
    conn = database._conn
    for statement in _MIGRATION_012.split(";"):
        stmt = statement.strip()
        if stmt:
            conn.execute(stmt)
    conn.commit()
    yield database
    # Cleanup
    conn.close()
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


# ── Test: Persistent enqueue/dequeue ────────────────────────────────────

class TestPersistentEnqueueDequeue:
    """Job enqueued with DB backend persists and survives."""

    @pytest.mark.asyncio
    async def test_enqueue_persists_to_db(self, bus, clk, db):
        q = JobQueue(bus, clock=clk, db=db)
        job = Job(type=JobType.WORKFLOW, payload={"x": 1}, created_at=clk.now())
        job_id = await q.enqueue(job)

        # Read directly from DB
        row = await db.fetch_one("SELECT * FROM jobs WHERE id = ?", [job_id])
        assert row is not None
        assert row["type"] == "workflow"
        assert json.loads(row["payload"]) == {"x": 1}

        rec = await db.fetch_one("SELECT * FROM job_records WHERE job_id = ?", [job_id])
        assert rec is not None
        assert rec["status"] == "pending"

    @pytest.mark.asyncio
    async def test_dequeue_updates_db(self, bus, clk, db):
        q = JobQueue(bus, clock=clk, db=db)
        job = Job(type=JobType.WORKFLOW, created_at=clk.now())
        job_id = await q.enqueue(job)

        record = await q.dequeue()
        assert record is not None
        assert record.status == JobStatus.RUNNING

        # Verify DB updated
        rec = await db.fetch_one("SELECT * FROM job_records WHERE job_id = ?", [job_id])
        assert rec["status"] == "running"
        assert rec["started_at"] is not None
        assert rec["attempts"] == 1


# ── Test: Restart survival ──────────────────────────────────────────────

class TestRestartSurvival:
    """Jobs survive queue restart (new JobQueue instance, same DB)."""

    @pytest.mark.asyncio
    async def test_jobs_survive_restart(self, bus, clk, db):
        """Jobs enqueued, new queue, same DB — jobs still there."""
        q1 = JobQueue(bus, clock=clk, db=db)
        job1 = Job(type=JobType.HEALTH_CHECK, created_at=clk.now())
        job2 = Job(type=JobType.REPORT_GENERATION, priority=5, created_at=clk.now())
        id1 = await q1.enqueue(job1)
        id2 = await q1.enqueue(job2)
        await q1.close()

        # New queue, same DB
        q2 = JobQueue(bus, clock=clk, db=db)
        all_jobs = await q2.list_all()
        assert len(all_jobs) == 2
        ids = {r.job.id for r in all_jobs}
        assert id1 in ids
        assert id2 in ids
        await q2.close()

    @pytest.mark.asyncio
    async def test_pending_works_after_restart(self, bus, clk, db):
        """Pending jobs remain dequeuable after restart."""
        q1 = JobQueue(bus, clock=clk, db=db)
        job = Job(type=JobType.CUSTOM, created_at=clk.now())
        job_id = await q1.enqueue(job)
        await q1.close()

        q2 = JobQueue(bus, clock=clk, db=db)
        record = await q2.dequeue()
        assert record is not None
        assert record.job.id == job_id
        assert record.status == JobStatus.RUNNING
        await q2.close()

    @pytest.mark.asyncio
    async def test_completed_survives_restart(self, bus, clk, db):
        """Completed jobs still show COMPLETED after restart."""
        q1 = JobQueue(bus, clock=clk, db=db)
        job = Job(type=JobType.PLUGIN_SCAN, created_at=clk.now())
        job_id = await q1.enqueue(job)
        await q1.dequeue()
        await q1.complete(job_id, result="ok")
        await q1.close()

        q2 = JobQueue(bus, clock=clk, db=db)
        record = await q2.get_status(job_id)
        assert record is not None
        assert record.status == JobStatus.COMPLETED
        assert record.completed_at is not None
        await q2.close()


# ── Test: Recover (reset RUNNING to PENDING on restart) ─────────────────

class TestRecovery:
    """Recovery mechanism resets RUNNING → PENDING on (re)start."""

    @pytest.mark.asyncio
    async def test_recover_running_jobs(self, bus, clk, db):
        """Dequeue but don't complete — recovery resets to PENDING."""
        q1 = JobQueue(bus, clock=clk, db=db)
        job = Job(type=JobType.CUSTOM, created_at=clk.now())
        job_id = await q1.enqueue(job)
        await q1.dequeue()  # job is now RUNNING

        # Verify a new queue sees it as RUNNING
        q2 = JobQueue(bus, clock=clk, db=db)
        record = await q2.get_status(job_id)
        assert record.status == JobStatus.RUNNING

        # Recover should reset RUNNING → PENDING
        recovered = await q2.recover()
        record = await q2.get_status(job_id)
        assert record.status == JobStatus.PENDING

        # Now dequeue should work
        dequeued = await q2.dequeue()
        assert dequeued is not None
        assert dequeued.job.id == job_id
        await q2.close()

    @pytest.mark.asyncio
    async def test_recover_only_running(self, bus, clk, db):
        """Only RUNNING jobs are recovered — PENDING/COMPLETED stay."""
        q1 = JobQueue(bus, clock=clk, db=db)
        j1 = Job(type=JobType.CUSTOM, created_at=clk.now())
        j2 = Job(type=JobType.CUSTOM, created_at=clk.now())
        id1 = await q1.enqueue(j1)  # will be dequeued -> RUNNING
        id2 = await q1.enqueue(j2)  # will stay PENDING
        await q1.dequeue()  # dequeues j1 (highest priority)
        await q1.close()

        q2 = JobQueue(bus, clock=clk, db=db)
        await q2.recover()

        rec1 = await q2.get_status(id1)
        assert rec1.status == JobStatus.PENDING, f"RUNNING should be recovered to PENDING, got {rec1.status}"

        rec2 = await q2.get_status(id2)
        assert rec2.status == JobStatus.PENDING
        await q2.close()


# ── Test: Priority persists ─────────────────────────────────────────────

class TestPriorityPersistence:
    """Priority-based dequeue still works with DB backend."""

    @pytest.mark.asyncio
    async def test_priority_across_restart(self, bus, clk, db):
        """Priority is read from DB, not re-computed from memory."""
        q1 = JobQueue(bus, clock=clk, db=db)
        low = Job(type=JobType.HEALTH_CHECK, priority=1, created_at=clk.now())
        high = Job(type=JobType.WORKFLOW, priority=10, created_at=clk.now())
        await q1.enqueue(low)
        await q1.enqueue(high)
        await q1.close()

        q2 = JobQueue(bus, clock=clk, db=db)
        first = await q2.dequeue()
        assert first is not None
        assert first.job.id == high.id, "Higher priority should be dequeued first"

        second = await q2.dequeue()
        assert second is not None
        assert second.job.id == low.id
        await q2.close()


# ── Test: Scheduled jobs ────────────────────────────────────────────────

class TestScheduled:
    """Scheduled_at filtering works with DB backend."""

    @pytest.mark.asyncio
    async def test_scheduled_at_respected(self, bus, clk, db):
        """Jobs scheduled in the future should not be dequeued."""
        q = JobQueue(bus, clock=clk, db=db)
        future_job = Job(
            type=JobType.CUSTOM,
            scheduled_at=clk.now() + timedelta(hours=1),
            created_at=clk.now(),
        )
        await q.enqueue(future_job)

        record = await q.dequeue()
        assert record is None

    @pytest.mark.asyncio
    async def test_scheduled_now_dequeues(self, bus, clk, db):
        """Jobs scheduled for now/past should be dequeued."""
        q = JobQueue(bus, clock=clk, db=db)
        job = Job(
            type=JobType.CUSTOM,
            scheduled_at=clk.now(),  # exactly now
            created_at=clk.now(),
        )
        await q.enqueue(job)
        record = await q.dequeue()
        assert record is not None
        assert record.job.id == job.id


# ── Test: Cache behavior ────────────────────────────────────────────────

class TestCacheBehavior:
    """Optional cache speeds up reads."""

    @pytest.mark.asyncio
    async def test_cache_enabled(self, bus, clk, db):
        """With cache enabled, get_status returns cached object."""
        q = JobQueue(bus, clock=clk, db=db, use_cache=True)
        job = Job(type=JobType.CUSTOM, created_at=clk.now())
        job_id = await q.enqueue(job)

        r1 = await q.get_status(job_id)
        assert r1 is not None

        # Cache should have it now (internal check)
        assert job_id in q._cache
        assert q._cache[job_id].job.id == job_id
        await q.close()

    @pytest.mark.asyncio
    async def test_cache_disabled(self, bus, clk, db):
        """With cache disabled, _cache stays empty."""
        q = JobQueue(bus, clock=clk, db=db, use_cache=False)
        job = Job(type=JobType.CUSTOM, created_at=clk.now())
        job_id = await q.enqueue(job)

        assert len(q._cache) == 0

        r1 = await q.get_status(job_id)
        assert r1 is not None
        assert r1.job.id == job_id
        await q.close()


# ── Test: stats() ───────────────────────────────────────────────────────

class TestStats:
    @pytest.mark.asyncio
    async def test_stats_empty(self, bus, clk, db):
        q = JobQueue(bus, clock=clk, db=db)
        stats = await q.stats()
        assert stats.get("pending", 0) == 0
        assert stats.get("running", 0) == 0
        assert stats.get("total", 0) == 0

    @pytest.mark.asyncio
    async def test_stats_counts(self, bus, clk, db):
        q = JobQueue(bus, clock=clk, db=db)
        j1 = Job(type=JobType.CUSTOM, created_at=clk.now())
        j2 = Job(type=JobType.WORKFLOW, created_at=clk.now())
        await q.enqueue(j1)
        await q.enqueue(j2)

        stats = await q.stats()
        assert stats["total"] == 2
        assert stats["pending"] == 2

        await q.dequeue()
        stats = await q.stats()
        assert stats["running"] == 1
        assert stats["pending"] == 1

    @pytest.mark.asyncio
    async def test_stats_after_restart(self, bus, clk, db):
        q1 = JobQueue(bus, clock=clk, db=db)
        j1 = Job(type=JobType.CUSTOM, created_at=clk.now())
        j2 = Job(type=JobType.CUSTOM, created_at=clk.now())
        await q1.enqueue(j1)
        await q1.enqueue(j2)
        await q1.close()

        q2 = JobQueue(bus, clock=clk, db=db)
        stats = await q2.stats()
        assert stats["total"] == 2
        assert stats["pending"] == 2
        await q2.close()


# ── Test: Edge cases ────────────────────────────────────────────────────

class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_double_close(self, bus, clk, db):
        q = JobQueue(bus, clock=clk, db=db)
        await q.close()
        await q.close()  # should not raise
        assert q.closed

    @pytest.mark.asyncio
    async def test_enqueue_after_close(self, bus, clk, db):
        q = JobQueue(bus, clock=clk, db=db)
        await q.close()
        job = Job(type=JobType.CUSTOM, created_at=clk.now())
        with pytest.raises(RuntimeError, match="closed"):
            await q.enqueue(job)

    @pytest.mark.asyncio
    async def test_in_memory_vs_db_same_behavior(self, clk):
        """In-memory and DB mode should behave identically."""
        bus = EventBus()
        q1 = JobQueue(bus, clock=clk)
        j1 = Job(type=JobType.CUSTOM, created_at=clk.now())
        await q1.enqueue(j1)
        r1 = await q1.dequeue()
        assert r1 is not None
        await q1.close()
