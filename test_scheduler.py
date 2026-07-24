import asyncio
import sys
from datetime import datetime

from src.sam.core.scheduler import Scheduler
from src.sam.core.job_queue import JobQueue
from src.sam.core.job import Job, JobType, JobStatus
from src.sam.core.event_bus import EventBus
from src.sam.core.clock import VirtualClock, FrozenClock, SystemClock


async def run_with_timeout(coro, timeout=10):
    return await asyncio.wait_for(coro, timeout=timeout)


async def test_register_handler_and_execute():
    bus = EventBus()
    clk = VirtualClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)
    sched = Scheduler(q, bus, clock=clk, interval=0.01)

    executed = []

    async def workflow_handler(job: Job):
        executed.append(job.id)
        return {"status": "ok"}

    sched.register_handler(JobType.WORKFLOW, workflow_handler)
    await sched.initialize()
    await sched.start()

    job = Job(type=JobType.WORKFLOW, payload={}, created_at=clk.now())
    await q.enqueue(job)

    # Wait for scheduler to pick it up — use real sleep for event loop yielding
    await asyncio.sleep(0.1)

    sched._running = False
    if sched._task:
        sched._task.cancel()
        try:
            await sched._task
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        sched._task = None

    status = await q.get_status(job.id)
    assert status.status == JobStatus.COMPLETED, f"Expected completed, got {status.status}"
    assert len(executed) == 1

    print("test_register_handler_and_execute: OK")


async def test_job_without_handler_fails():
    bus = EventBus()
    clk = VirtualClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)
    sched = Scheduler(q, bus, clock=clk, interval=0.01)

    await sched.initialize()
    await sched.start()

    job = Job(type=JobType.HEALTH_CHECK, payload={}, created_at=clk.now())
    await q.enqueue(job)

    await asyncio.sleep(0.1)

    sched._running = False
    if sched._task:
        sched._task.cancel()
        try:
            await sched._task
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        sched._task = None

    status = await q.get_status(job.id)
    assert status.status == JobStatus.FAILED, f"Expected failed, got {status.status}"
    assert "No handler registered" in status.error

    print("test_job_without_handler_fails: OK")


async def test_job_retry_on_failure():
    bus = EventBus()
    clk = VirtualClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)
    sched = Scheduler(q, bus, clock=clk, interval=0.01)

    attempts = []

    async def flaky_handler(job: Job):
        attempts.append(job.id)
        raise ValueError("Timeout")

    sched.register_handler(JobType.KNOWLEDGE_IMPORT, flaky_handler)
    await sched.initialize()
    await sched.start()

    job = Job(type=JobType.KNOWLEDGE_IMPORT, max_attempts=2, payload={}, created_at=clk.now())
    await q.enqueue(job)

    await asyncio.sleep(0.2)

    sched._running = False
    if sched._task:
        sched._task.cancel()
        try:
            await sched._task
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        sched._task = None

    status = await q.get_status(job.id)
    # After first fail + retry, scheduler picks it up again -> fail -> check max_attempts
    # max_attempts=2, so after 2 failures it should remain FAILED
    assert status.status == JobStatus.FAILED, f"Expected failed, got {status.status}"

    print("test_job_retry_on_failure: OK")


async def test_stop_scheduler():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)
    sched = Scheduler(q, bus, clock=clk, interval=0.01)

    await sched.initialize()
    await sched.start()

    await asyncio.sleep(0.05)

    h = await sched.health()
    assert "running" in h.message

    await sched.stop()
    h2 = await sched.health()
    assert "stopped" in h2.message

    print("test_stop_scheduler: OK")


async def test_scheduler_health_with_metrics():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 0, 0, 0))
    q = JobQueue(bus, clock=clk)
    sched = Scheduler(q, bus, clock=clk, interval=5.0)

    async def handler(job):
        return {}

    sched.register_handler(JobType.WORKFLOW, handler)
    await sched.initialize()
    await sched.start()

    h = await sched.health()
    assert h.status.value == "healthy"
    assert h.metrics["interval"] == 5.0
    assert h.metrics["running"] is True

    await sched.stop()
    print("test_scheduler_health_with_metrics: OK")


if __name__ == "__main__":
    tests = [
        test_register_handler_and_execute,
        test_job_without_handler_fails,
        test_job_retry_on_failure,
        test_stop_scheduler,
        test_scheduler_health_with_metrics,
    ]
    for t in tests:
        try:
            asyncio.run(t())
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"{t.__name__}: FAILED ({e})")
            sys.exit(1)
    print("ALL PASSED")
    sys.exit(0)
