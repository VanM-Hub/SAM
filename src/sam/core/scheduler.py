from __future__ import annotations

import asyncio
import structlog
from typing import Dict, Callable, Awaitable, Any, Optional
from datetime import datetime

from .service import RuntimeService
from .health import ServiceHealth, HealthStatus
from .job_queue import JobQueue
from .job import Job, JobRecord, JobType
from .event_bus import EventBus
from .clock import TimeProvider, SystemClock
from .events import JobStarted, JobCompleted, JobFailed


class Scheduler(RuntimeService):
    """Scheduler service that polls JobQueue and executes jobs."""

    def __init__(
        self,
        job_queue: JobQueue,
        event_bus: EventBus,
        clock: Optional[TimeProvider] = None,
        interval: float = 5.0,
    ):
        self._job_queue = job_queue
        self._event_bus = event_bus
        self._clock = clock or SystemClock()
        self._interval = interval
        self._logger = structlog.get_logger()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._handlers: Dict[JobType, Callable[[Job], Awaitable[Any]]] = {}

    @property
    def name(self) -> str:
        return "scheduler"

    def register_handler(self, job_type: JobType, handler: Callable[[Job], Awaitable[Any]]) -> None:
        """Register a handler for a job type."""
        self._handlers[job_type] = handler
        self._logger.info("handler_registered", job_type=job_type.value)

    async def initialize(self) -> None:
        """Initialize scheduler."""
        self._logger.info("scheduler_initialized")
        self._initialized = True

    async def start(self) -> None:
        """Start the scheduler loop."""
        if not self._initialized:
            raise RuntimeError("Scheduler not initialized")
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        self._logger.info("scheduler_started", interval=self._interval)

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._logger.info("scheduler_stopped")

    async def health(self) -> ServiceHealth:
        """Return scheduler health."""
        status = HealthStatus.HEALTHY if self._running else HealthStatus.DEGRADED
        return ServiceHealth(
            status=status,
            message=f"Scheduler is {'running' if self._running else 'stopped'}",
            metrics={
                "interval": self._interval,
                "running": self._running,
                "handlers": list(self._handlers.keys()),
            },
            last_check=self._clock.now(),
        )

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                record = await self._job_queue.dequeue()
                if record:
                    await self._execute_job(record)
                else:
                    # Always yield to event loop even with VirtualClock
                    await self._clock.sleep(self._interval)
                    await asyncio.sleep(0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("scheduler_loop_error", error=str(e))
                await self._clock.sleep(self._interval)
                await asyncio.sleep(0)

    async def _execute_job(self, record: JobRecord) -> None:
        """Execute a single job."""
        job = record.job
        handler = self._handlers.get(job.type)

        if not handler:
            error = f"No handler registered for job type: {job.type}"
            self._logger.error("no_handler_for_job", job_id=job.id, job_type=job.type.value)
            await self._job_queue.fail(job.id, error)
            # No handler = no point retrying, job stays FAILED
            return

        try:
            result = await handler(job)
            await self._job_queue.complete(job.id, result)
            self._logger.info("job_executed", job_id=job.id, job_type=job.type.value)
        except Exception as e:
            error = str(e)
            self._logger.error("job_execution_failed", job_id=job.id, error=error)

            await self._job_queue.fail(job.id, error)

            # If attempts < max_attempts, retry
            if record.attempts < job.max_attempts:
                await self._job_queue.retry(job.id)
                self._logger.info("job_retried", job_id=job.id, attempts=record.attempts + 1)
