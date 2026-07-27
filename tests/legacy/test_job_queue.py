import asyncio
import sys
from datetime import datetime, timedelta

from src.sam.core.job import Job, JobType, JobStatus
from src.sam.core.job_queue import JobQueue
from src.sam.core.event_bus import EventBus
from src.sam.core.clock import FrozenClock, VirtualClock


async def test_enqueue_dequeue():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)

    job = Job(type=JobType.WORKFLOW, payload={"name": "test"}, created_at=clk.now())
    job_id = await q.enqueue(job)

    record = await q.dequeue()
    assert record is not None
    assert record.job.id == job_id
    assert record.status == JobStatus.RUNNING
    assert record.started_at == clk.now()
    assert record.attempts == 1

    # Queue should be empty now
    none_record = await q.dequeue()
    assert none_record is None

    print("test_enqueue_dequeue: OK")


async def test_priority_ordering():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)

    low = Job(type=JobType.HEALTH_CHECK, priority=1, created_at=clk.now())
    high = Job(type=JobType.WORKFLOW, priority=10, created_at=clk.now())

    await q.enqueue(low)
    await q.enqueue(high)

    first = await q.dequeue()
    assert first.job.id == high.id, "Higher priority should be dequeued first"

    second = await q.dequeue()
    assert second.job.id == low.id

    print("test_priority_ordering: OK")


async def test_complete():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)

    job = Job(type=JobType.REPORT_GENERATION, created_at=clk.now())
    await q.enqueue(job)
    await q.dequeue()

    await q.complete(job.id, result={"report": "done"})
    status = await q.get_status(job.id)
    assert status.status == JobStatus.COMPLETED
    assert status.completed_at is not None

    print("test_complete: OK")


async def test_fail():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)

    job = Job(type=JobType.PLUGIN_SCAN, created_at=clk.now())
    await q.enqueue(job)
    await q.dequeue()

    await q.fail(job.id, "plugin not found")
    status = await q.get_status(job.id)
    assert status.status == JobStatus.FAILED
    assert "plugin not found" in status.error

    print("test_fail: OK")


async def test_cancel():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)

    job = Job(type=JobType.MIGRATION, created_at=clk.now())
    await q.enqueue(job)

    await q.cancel(job.id)
    status = await q.get_status(job.id)
    assert status.status == JobStatus.CANCELLED

    print("test_cancel: OK")


async def test_retry():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)

    job = Job(type=JobType.KNOWLEDGE_IMPORT, max_attempts=3, created_at=clk.now())
    await q.enqueue(job)
    await q.dequeue()
    await q.fail(job.id, "timeout")

    await q.retry(job.id)
    status = await q.get_status(job.id)
    assert status.status == JobStatus.PENDING
    assert status.error is None

    # Dequeue again (should be possible after retry)
    record = await q.dequeue()
    assert record.job.id == job.id
    assert record.attempts == 2  # retry preserved attempt count, dequeue incremented

    print("test_retry: OK")


async def test_retry_max_attempts():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)

    job = Job(type=JobType.CUSTOM, max_attempts=1, created_at=clk.now())
    await q.enqueue(job)
    await q.dequeue()
    await q.fail(job.id, "failed")

    try:
        await q.retry(job.id)
        assert False, "Should have raised ValueError for max attempts exceeded"
    except ValueError as e:
        assert "exceeded max attempts" in str(e)

    print("test_retry_max_attempts: OK")


async def test_event_publishing():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)

    received = []

    async def handler(ev):
        received.append(ev.type)

    bus.subscribe("job.enqueued", handler)
    bus.subscribe("job.started", handler)
    bus.subscribe("job.completed", handler)
    bus.subscribe("job.failed", handler)

    job = Job(type=JobType.CUSTOM, created_at=clk.now())
    await q.enqueue(job)
    await q.dequeue()
    await q.complete(job.id)

    await asyncio.sleep(0)  # yield for handler

    assert "job.enqueued" in received
    assert "job.started" in received
    assert "job.completed" in received

    # Also test fail event
    job2 = Job(type=JobType.CUSTOM, created_at=clk.now())
    await q.enqueue(job2)
    await q.dequeue()
    await q.fail(job2.id, "error")
    await asyncio.sleep(0)

    assert "job.failed" in received

    print("test_event_publishing: OK")


if __name__ == "__main__":
    tests = [
        test_enqueue_dequeue,
        test_priority_ordering,
        test_complete,
        test_fail,
        test_cancel,
        test_retry,
        test_retry_max_attempts,
        test_event_publishing,
    ]
    for t in tests:
        try:
            asyncio.run(t())
        except Exception as e:
            print(f"{t.__name__}: FAILED ({e})")
            sys.exit(1)
    print("ALL PASSED")
    sys.exit(0)
