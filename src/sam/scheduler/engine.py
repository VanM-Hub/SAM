"""Scheduler engine for running scheduled workflows."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog

from sam.persistence.database import Database
from sam.persistence.repositories import ScheduleRepository
from sam.workflow.engine import WorkflowEngine
from sam.runtime.registry import CapabilityRegistry
from sam.scheduler.models import Schedule, ScheduleStatus, ScheduleType

logger = structlog.get_logger(__name__)


class SchedulerEngine:
    """Engine for executing scheduled workflows."""

    def __init__(
        self,
        db: Database,
        workflow_engine: WorkflowEngine,
        registry: CapabilityRegistry,
    ):
        self._db = db
        self._workflow_engine = workflow_engine
        self._registry = registry
        self._schedule_repo = ScheduleRepository(db)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._check_interval = 1.0  # Check every second

    async def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("SchedulerEngine started")

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("SchedulerEngine stopped")

    async def add(self, schedule: Schedule) -> str:
        """Add a new schedule."""
        # Compute next run time
        schedule.next_run = schedule.compute_next_run()

        # Convert to dict for storage
        schedule_dict = {
            "id": schedule.id,
            "name": schedule.name,
            "workflow_file": schedule.workflow_file,
            "schedule_type": schedule.schedule_type.value,
            "cron_expression": schedule.cron_expression,
            "delay_seconds": schedule.delay_seconds,
            "max_retries": schedule.max_retries,
            "retry_delay": schedule.retry_delay,
            "enabled": schedule.enabled,
            "status": schedule.status.value,
            "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "created_at": schedule.created_at.isoformat(),
            "updated_at": schedule.updated_at.isoformat(),
            "run_count": schedule.run_count,
            "last_error": schedule.last_error,
            "metadata": schedule.metadata,
        }

        await self._schedule_repo.create(schedule_dict)
        logger.info("Schedule added", schedule_id=schedule.id, name=schedule.name, next_run=schedule.next_run)
        return schedule.id

    async def cancel(self, schedule_id: str) -> None:
        """Cancel a schedule."""
        await self._schedule_repo.update(schedule_id, {
            "status": ScheduleStatus.DISABLED.value,
            "enabled": False,
            "updated_at": datetime.utcnow().isoformat(),
        })
        logger.info("Schedule cancelled", schedule_id=schedule_id)

    async def enable(self, schedule_id: str) -> None:
        """Enable a disabled schedule."""
        schedule = await self._schedule_repo.get(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule not found: {schedule_id}")

        # Recompute next run
        now = datetime.utcnow()
        next_run = None
        if schedule["schedule_type"] == ScheduleType.CRON.value and schedule["cron_expression"]:
            try:
                from croniter import croniter
                cron = croniter(schedule["cron_expression"], now)
                next_run = cron.get_next(datetime)
            except ImportError:
                # Fallback: just run soon
                from datetime import timedelta
                next_run = now + timedelta(hours=1)
        elif schedule["schedule_type"] == ScheduleType.INTERVAL.value:
            from datetime import timedelta
            next_run = now + timedelta(seconds=schedule["delay_seconds"] or 60)
        else:
            next_run = now

        await self._schedule_repo.update(schedule_id, {
            "status": ScheduleStatus.PENDING.value,
            "enabled": True,
            "next_run": next_run.isoformat() if next_run else None,
            "updated_at": datetime.utcnow().isoformat(),
        })
        logger.info("Schedule enabled", schedule_id=schedule_id)

    async def list(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all schedules."""
        return await self._schedule_repo.list(limit)

    async def get(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get a schedule by ID."""
        return await self._schedule_repo.get(schedule_id)

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop - checks for due schedules."""
        while self._running:
            try:
                await self._process_pending()
            except Exception as e:
                logger.error("Scheduler loop error", error=str(e))
            await asyncio.sleep(self._check_interval)

    async def _process_pending(self) -> None:
        """Process schedules that are due to run."""
        pending = await self._schedule_repo.get_pending()
        now = datetime.utcnow()

        for schedule in pending:
            # Check if due
            next_run_str = schedule.get("next_run")
            if next_run_str:
                next_run = datetime.fromisoformat(next_run_str)
                if next_run > now:
                    continue

            # Check if already running
            if schedule["status"] == ScheduleStatus.RUNNING.value:
                logger.warning("Schedule already running, skipping", schedule_id=schedule["id"])
                continue

            # Execute workflow
            await self._execute_workflow(schedule)

    async def _execute_workflow(self, schedule: Dict[str, Any]) -> None:
        """Execute a workflow for the schedule."""
        schedule_id = schedule["id"]
        workflow_file = schedule["workflow_file"]
        max_retries = schedule["max_retries"]
        retry_delay = schedule["retry_delay"]

        # Mark as running
        await self._schedule_repo.update(schedule_id, {
            "status": ScheduleStatus.RUNNING.value,
            "updated_at": datetime.utcnow().isoformat(),
        })

        logger.info("Executing scheduled workflow", schedule_id=schedule_id, workflow_file=workflow_file)

        for attempt in range(max_retries + 1):
            try:
                # Run workflow
                result = await self._workflow_engine.execute_workflow(
                    workflow_file=workflow_file,
                    inputs={},
                )

                # Success - update schedule
                now = datetime.utcnow()
                next_run = self._compute_next_run(schedule, now)

                await self._schedule_repo.update(schedule_id, {
                    "status": ScheduleStatus.PENDING.value if schedule["schedule_type"] != ScheduleType.ONCE.value else ScheduleStatus.COMPLETED.value,
                    "last_run": now.isoformat(),
                    "next_run": next_run.isoformat() if next_run else None,
                    "run_count": schedule["run_count"] + 1,
                    "last_error": None,
                    "updated_at": now.isoformat(),
                })

                logger.info("Scheduled workflow completed", schedule_id=schedule_id, workflow_id=result.get("workflow_id"))
                return

            except Exception as e:
                error_msg = str(e)
                logger.warning("Scheduled workflow attempt failed", schedule_id=schedule_id, attempt=attempt + 1, error=error_msg)

                if attempt < max_retries:
                    # Wait before retry
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # All retries exhausted
                    now = datetime.utcnow()
                    await self._schedule_repo.update(schedule_id, {
                        "status": ScheduleStatus.FAILED.value,
                        "last_run": now.isoformat(),
                        "run_count": schedule["run_count"] + 1,
                        "last_error": error_msg,
                        "updated_at": now.isoformat(),
                    })
                    logger.error("Scheduled workflow failed after retries", schedule_id=schedule_id, error=error_msg)
                    return

    def _compute_next_run(self, schedule: Dict[str, Any], from_time: datetime) -> Optional[datetime]:
        """Compute next run time for a schedule dict."""
        schedule_type = schedule["schedule_type"]

        if schedule_type == ScheduleType.ONCE.value:
            return None  # One-time only

        elif schedule_type == ScheduleType.INTERVAL.value:
            delay = schedule.get("delay_seconds") or 60
            from datetime import timedelta
            return from_time + timedelta(seconds=delay)

        elif schedule_type == ScheduleType.CRON.value:
            cron_expr = schedule.get("cron_expression")
            if not cron_expr:
                return None
            try:
                from croniter import croniter
                cron = croniter(cron_expr, from_time)
                return cron.get_next(datetime)
            except ImportError:
                from datetime import timedelta
                return from_time + timedelta(hours=1)

        return None