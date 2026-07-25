from __future__ import annotations

import asyncio
import structlog
from typing import Dict, Callable, Awaitable, Any, Optional, TYPE_CHECKING
from datetime import datetime

from .service import RuntimeService
from .health import ServiceHealth, HealthStatus
from .job_queue import JobQueue
from .job import Job, JobRecord, JobType
from .event_bus import EventBus
from .clock import TimeProvider, SystemClock
from .events import JobStarted, JobCompleted, JobFailed

if TYPE_CHECKING:
    from ..cluster.leader import LeaderElection


class Scheduler(RuntimeService):
    """Scheduler service that polls JobQueue and executes jobs.

    When clustering is enabled (leader_election provided), the scheduler
    only executes jobs if the current node is the cluster leader.
    Non-leader nodes idle but remain healthy (DEGRADED status).
    """

    def __init__(
        self,
        job_queue: JobQueue,
        event_bus: EventBus,
        clock: Optional[TimeProvider] = None,
        interval: float = 5.0,
        leader_election: Optional["LeaderElection"] = None,
        cluster_enabled: bool = False,
        max_idle_cycles_before_log: int = 20,
    ):
        self._job_queue = job_queue
        self._event_bus = event_bus
        self._clock = clock or SystemClock()
        self._interval = interval
        self._leader_election = leader_election
        self._cluster_enabled = cluster_enabled
        self._max_idle_cycles_before_log = max_idle_cycles_before_log
        self._logger = structlog.get_logger()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._handlers: Dict[JobType, Callable[[Job], Awaitable[Any]]] = {}
        self._idle_cycle_count: int = 0
        self._is_leader: bool = False

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

        # Check leader status before starting (only if leader_election provided)
        if self._cluster_enabled and self._leader_election:
            self._is_leader = await self._leader_election.is_leader()
            if not self._is_leader:
                self._logger.info(
                    "scheduler_not_leader",
                    message="Scheduler started but not leader — idle mode",
                )
        else:
            self._is_leader = False  # standalone, not leader by default

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        self._logger.info(
            "scheduler_started",
            interval=self._interval,
            is_leader=self._is_leader,
            cluster_enabled=self._cluster_enabled,
        )

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
        if not self._running:
            return ServiceHealth(
                status=HealthStatus.DEGRADED,
                message="Scheduler is stopped",
                metrics={
                    "interval": self._interval,
                    "running": False,
                    "handlers": list(self._handlers.keys()),
                    "cluster_enabled": self._cluster_enabled,
                    "is_leader": self._is_leader,
                },
                last_check=self._clock.now(),
            )

        # Running: determine status
        if self._cluster_enabled and not self._is_leader:
            status = HealthStatus.HEALTHY  # idle is healthy, just not executing
            message = "Scheduler is running (idle — not leader)"
        else:
            status = HealthStatus.HEALTHY
            message = "Scheduler is running"

        return ServiceHealth(
            status=status,
            message=message,
            metrics={
                "interval": self._interval,
                "running": self._running,
                "handlers": list(self._handlers.keys()),
                "cluster_enabled": self._cluster_enabled,
                "is_leader": self._is_leader,
                "idle_cycle_count": self._idle_cycle_count,
            },
            last_check=self._clock.now(),
        )

    async def _run_loop(self) -> None:
        """Main scheduler loop.

        In cluster mode, periodically re-checks leadership. Non-leader nodes
        skip job execution but remain healthy (idle mode).
        """
        while self._running:
            try:
                # Leader check: if clustering enabled with leader_election, re-verify
                if self._cluster_enabled and self._leader_election:
                    self._is_leader = await self._leader_election.is_leader()

                # Only skip if BOTH cluster enabled AND we have a leader election
                # AND we're not the leader. cluster_enabled without leader_election
                # means standalone mode.
                if self._cluster_enabled and self._leader_election and not self._is_leader:
                    self._idle_cycle_count += 1
                    if self._idle_cycle_count % self._max_idle_cycles_before_log == 1:
                        self._logger.debug(
                            "scheduler_idle_not_leader",
                            idle_cycles=self._idle_cycle_count,
                        )
                    await self._clock.sleep(self._interval)
                    await asyncio.sleep(0)
                    continue

                # Leader or standalone: execute normally
                self._idle_cycle_count = 0
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
