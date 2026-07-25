"""
Tests for Scheduler (cluster-aware + legacy behavior)
Pattern: inline replica classes, pytest-asyncio.
"""

from __future__ import annotations

import pytest
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.sam.core.scheduler import Scheduler
from src.sam.core.job_queue import JobQueue
from src.sam.core.job import Job, JobType, JobStatus
from src.sam.core.event_bus import EventBus
from src.sam.core.clock import VirtualClock, FrozenClock
from src.sam.core.health import HealthStatus


# ── Inline Replicas ───────────────────────────────────────────────────


class _LeaderRecord:
    def __init__(self, leader_id: str, cluster_id: str = "test-cluster"):
        self.leader_id = leader_id
        self.cluster_id = cluster_id


class _LeaderElection:
    def __init__(self, is_leader: bool = True, leader_id: str = "node-a"):
        self._is_leader = is_leader
        self._leader_id = leader_id
        self.is_leader_calls: List[bool] = []  # track calls

    async def is_leader(self) -> bool:
        self.is_leader_calls.append(self._is_leader)
        return self._is_leader

    def set_leader(self, value: bool):
        self._is_leader = value


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def clock():
    return VirtualClock(datetime(2026, 7, 25, 0, 0, 0))


@pytest.fixture
def job_queue(event_bus, clock):
    return JobQueue(event_bus, clock=clock)


@pytest.fixture
def leader_election_leader():
    return _LeaderElection(is_leader=True, leader_id="node-a")


@pytest.fixture
def leader_election_follower():
    return _LeaderElection(is_leader=False, leader_id="node-b")


# ── 1. Legacy Scheduler Tests ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_handler_and_execute(job_queue, event_bus, clock):
    sched = Scheduler(job_queue, event_bus, clock=clock, interval=0.01)

    executed = []

    async def workflow_handler(job: Job):
        executed.append(job.id)
        return {"status": "ok"}

    sched.register_handler(JobType.WORKFLOW, workflow_handler)
    await sched.initialize()
    await sched.start()

    job = Job(type=JobType.WORKFLOW, payload={}, created_at=clock.now())
    await job_queue.enqueue(job)

    await asyncio.sleep(0.1)

    await sched.stop()

    status = await job_queue.get_status(job.id)
    assert status.status == JobStatus.COMPLETED
    assert len(executed) == 1


@pytest.mark.asyncio
async def test_job_without_handler_fails(job_queue, event_bus, clock):
    sched = Scheduler(job_queue, event_bus, clock=clock, interval=0.01)

    await sched.initialize()
    await sched.start()

    job = Job(type=JobType.HEALTH_CHECK, payload={}, created_at=clock.now())
    await job_queue.enqueue(job)

    await asyncio.sleep(0.1)

    await sched.stop()

    status = await job_queue.get_status(job.id)
    assert status.status == JobStatus.FAILED
    assert "No handler registered" in status.error


@pytest.mark.asyncio
async def test_job_retry_on_failure(job_queue, event_bus, clock):
    sched = Scheduler(job_queue, event_bus, clock=clock, interval=0.01)

    attempts = []

    async def flaky_handler(job: Job):
        attempts.append(job.id)
        raise ValueError("Timeout")

    sched.register_handler(JobType.KNOWLEDGE_IMPORT, flaky_handler)
    await sched.initialize()
    await sched.start()

    job = Job(type=JobType.KNOWLEDGE_IMPORT, max_attempts=2, payload={}, created_at=clock.now())
    await job_queue.enqueue(job)

    await asyncio.sleep(0.2)

    await sched.stop()

    status = await job_queue.get_status(job.id)
    assert status.status == JobStatus.FAILED


@pytest.mark.asyncio
async def test_stop_scheduler(job_queue, event_bus, clock):
    sched = Scheduler(job_queue, event_bus, clock=clock, interval=0.01)

    await sched.initialize()
    await sched.start()

    await asyncio.sleep(0.05)

    h = await sched.health()
    assert "running" in h.message

    await sched.stop()
    h2 = await sched.health()
    assert "stopped" in h2.message


@pytest.mark.asyncio
async def test_scheduler_health_with_metrics(job_queue, event_bus, clock):
    sched = Scheduler(job_queue, event_bus, clock=clock, interval=5.0)

    async def handler(job):
        return {}

    sched.register_handler(JobType.WORKFLOW, handler)
    await sched.initialize()
    await sched.start()

    h = await sched.health()
    assert h.status.value == "healthy"
    assert h.metrics["interval"] == 5.0
    assert h.metrics["running"] is True
    assert h.metrics["cluster_enabled"] is False

    await sched.stop()


# ── 2. Cluster-Aware Scheduler Tests ──────────────────────────────────


@pytest.mark.asyncio
async def test_leader_executes_jobs(job_queue, event_bus, clock, leader_election_leader):
    """Leader node should execute jobs normally."""
    sched = Scheduler(
        job_queue,
        event_bus,
        clock=clock,
        interval=0.01,
        leader_election=leader_election_leader,
        cluster_enabled=True,
    )

    executed = []

    async def handler(job: Job):
        executed.append(job.id)
        return {"status": "ok"}

    sched.register_handler(JobType.WORKFLOW, handler)
    await sched.initialize()
    await sched.start()

    job = Job(type=JobType.WORKFLOW, payload={}, created_at=clock.now())
    await job_queue.enqueue(job)

    await asyncio.sleep(0.1)

    await sched.stop()

    assert len(executed) == 1
    assert leader_election_leader.is_leader_calls, "is_leader() should have been called"


@pytest.mark.asyncio
async def test_non_leader_does_not_execute_jobs(job_queue, event_bus, clock, leader_election_follower):
    """Non-leader node should idle and not process any jobs."""
    sched = Scheduler(
        job_queue,
        event_bus,
        clock=clock,
        interval=0.01,
        leader_election=leader_election_follower,
        cluster_enabled=True,
        max_idle_cycles_before_log=100,  # prevent debug output in test
    )

    executed = []

    async def handler(job: Job):
        executed.append(job.id)
        return {"status": "ok"}

    sched.register_handler(JobType.WORKFLOW, handler)
    await sched.initialize()
    await sched.start()

    job = Job(type=JobType.WORKFLOW, payload={}, created_at=clock.now())
    await job_queue.enqueue(job)

    await asyncio.sleep(0.15)

    await sched.stop()

    # Non-leader should not have executed any job
    assert len(executed) == 0
    assert leader_election_follower.is_leader_calls, "is_leader() should have been called"


@pytest.mark.asyncio
async def test_non_leader_health_is_healthy_idle(job_queue, event_bus, clock, leader_election_follower):
    """Non-leader scheduler should report healthy with idle status."""
    sched = Scheduler(
        job_queue,
        event_bus,
        clock=clock,
        interval=0.01,
        leader_election=leader_election_follower,
        cluster_enabled=True,
    )

    await sched.initialize()
    await sched.start()

    await asyncio.sleep(0.05)

    h = await sched.health()
    assert h.status == HealthStatus.HEALTHY
    assert "idle" in h.message.lower()
    assert h.metrics["cluster_enabled"] is True
    assert h.metrics["is_leader"] is False

    await sched.stop()


@pytest.mark.asyncio
async def test_leader_health_reports_as_leader(job_queue, event_bus, clock, leader_election_leader):
    """Leader scheduler should report health with is_leader=True."""
    sched = Scheduler(
        job_queue,
        event_bus,
        clock=clock,
        interval=0.01,
        leader_election=leader_election_leader,
        cluster_enabled=True,
    )

    await sched.initialize()
    await sched.start()

    await asyncio.sleep(0.05)

    h = await sched.health()
    assert h.status == HealthStatus.HEALTHY
    assert "running" in h.message.lower()
    assert h.metrics["cluster_enabled"] is True
    assert h.metrics["is_leader"] is True

    await sched.stop()


@pytest.mark.asyncio
async def test_standalone_no_cluster_still_works(job_queue, event_bus, clock):
    """Without leader_election, scheduler should work as standalone."""
    sched = Scheduler(job_queue, event_bus, clock=clock, interval=0.01)

    executed = []

    async def handler(job: Job):
        executed.append(job.id)
        return {"status": "ok"}

    sched.register_handler(JobType.WORKFLOW, handler)
    await sched.initialize()
    await sched.start()

    job = Job(type=JobType.WORKFLOW, payload={}, created_at=clock.now())
    await job_queue.enqueue(job)

    await asyncio.sleep(0.1)

    await sched.stop()

    assert len(executed) == 1
    assert sched._is_leader is False  # default
    assert sched._cluster_enabled is False


@pytest.mark.asyncio
async def test_cluster_enabled_no_leader_election_still_works(job_queue, event_bus, clock):
    """cluster_enabled=True but no leader_election should still work standalone."""
    sched = Scheduler(
        job_queue, event_bus, clock=clock, interval=0.01, cluster_enabled=True
    )

    executed = []

    async def handler(job: Job):
        executed.append(job.id)
        return {"status": "ok"}

    sched.register_handler(JobType.WORKFLOW, handler)
    await sched.initialize()
    await sched.start()

    job = Job(type=JobType.WORKFLOW, payload={}, created_at=clock.now())
    await job_queue.enqueue(job)

    await asyncio.sleep(0.1)

    await sched.stop()

    # Should still execute — no leader_election means standalone
    assert len(executed) == 1


@pytest.mark.asyncio
async def test_start_checks_leader_on_init(job_queue, event_bus, clock, leader_election_follower):
    """start() should check leader status and log when not leader."""
    sched = Scheduler(
        job_queue,
        event_bus,
        clock=clock,
        interval=0.01,
        leader_election=leader_election_follower,
        cluster_enabled=True,
    )

    await sched.initialize()
    await sched.start()

    await asyncio.sleep(0.02)

    # is_leader should have been called at least once during start
    assert len(leader_election_follower.is_leader_calls) >= 1
    assert sched._is_leader is False

    await sched.stop()


@pytest.mark.asyncio
async def test_idle_cycle_tracking(job_queue, event_bus, clock, leader_election_follower):
    """Idle cycle count should increment when non-leader."""
    sched = Scheduler(
        job_queue,
        event_bus,
        clock=clock,
        interval=0.01,
        leader_election=leader_election_follower,
        cluster_enabled=True,
        max_idle_cycles_before_log=100,
    )

    await sched.initialize()
    await sched.start()

    await asyncio.sleep(0.1)

    h = await sched.health()
    assert h.metrics.get("idle_cycle_count", 0) > 0

    await sched.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
