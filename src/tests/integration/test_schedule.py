"""Integration tests for schedule management and automatic report generation."""

import pytest
import traceback
from datetime import datetime, timedelta

from sam.persistence.database import Database
from sam.scheduler.engine import SchedulerEngine
from sam.scheduler.models import Schedule, ScheduleType, ScheduleStatus
from sam.workflow.engine import WorkflowEngine
from sam.runtime.registry import CapabilityRegistry
from sam.runtime.runtime import CapabilityRuntime
from sam.events.event_bus import EventBus


@pytest.mark.asyncio
async def test_schedule_create_and_list(tmp_path):
    """Test schedule creation and listing via SchedulerEngine."""
    db_path = str(tmp_path / "sam.db")
    db = None
    try:
        db = Database(db_path)
        await db.initialize()

        event_bus = EventBus()
        registry = CapabilityRegistry()
        runtime = CapabilityRuntime(registry)
        workflow_engine = WorkflowEngine(runtime, registry, db, event_bus)
        scheduler = SchedulerEngine(db, workflow_engine, registry)

        # Create a schedule
        schedule = Schedule(
            name="test-schedule",
            workflow_file="examples/workflows/diagnose-runtime.yaml",
            schedule_type=ScheduleType.INTERVAL,
            delay_seconds=60,
            max_retries=2,
            retry_delay=30,
            enabled=True,
        )

        schedule_id = await scheduler.add(schedule)
        assert schedule_id is not None

        # List schedules
        schedules = await scheduler.list()
        assert len(schedules) == 1
        assert schedules[0]["name"] == "test-schedule"
        assert schedules[0]["schedule_type"] == "interval"
        assert schedules[0]["delay_seconds"] == 60
        assert schedules[0]["enabled"] == 1
        assert schedules[0]["status"] == "pending"

    except Exception as exc:
        pytest.fail(f"Schedule integration test failed: {exc}\n{traceback.format_exc()}")
    finally:
        if db:
            await db.close()


@pytest.mark.asyncio
async def test_schedule_cancel_and_enable(tmp_path):
    """Test schedule cancellation and re-enabling."""
    db_path = str(tmp_path / "sam.db")
    db = None
    try:
        db = Database(db_path)
        await db.initialize()

        event_bus = EventBus()
        registry = CapabilityRegistry()
        runtime = CapabilityRuntime(registry)
        workflow_engine = WorkflowEngine(runtime, registry, db, event_bus)
        scheduler = SchedulerEngine(db, workflow_engine, registry)

        schedule = Schedule(
            name="test-cancel",
            workflow_file="examples/workflows/diagnose-runtime.yaml",
            schedule_type=ScheduleType.INTERVAL,
            delay_seconds=60,
        )
        schedule_id = await scheduler.add(schedule)

        # Cancel schedule
        await scheduler.cancel(schedule_id)

        # Verify cancelled
        sched = await scheduler.get(schedule_id)
        assert sched["status"] == "disabled"
        assert sched["enabled"] == 0

        # Enable schedule
        await scheduler.enable(schedule_id)

        # Verify enabled
        sched = await scheduler.get(schedule_id)
        assert sched["status"] == "pending"
        assert sched["enabled"] == 1
        assert sched["next_run"] is not None

    except Exception as exc:
        pytest.fail(f"Schedule cancel/enable test failed: {exc}\n{traceback.format_exc()}")
    finally:
        if db:
            await db.close()


@pytest.mark.asyncio
async def test_schedule_persistence_and_reload(tmp_path):
    """Test schedule persists across engine restarts."""
    db_path = str(tmp_path / "sam.db")
    db = None
    try:
        db = Database(db_path)
        await db.initialize()

        event_bus = EventBus()
        registry = CapabilityRegistry()
        runtime = CapabilityRuntime(registry)
        workflow_engine = WorkflowEngine(runtime, registry, db, event_bus)
        scheduler = SchedulerEngine(db, workflow_engine, registry)

        schedule = Schedule(
            name="persist-test",
            workflow_file="examples/workflows/diagnose-runtime.yaml",
            schedule_type=ScheduleType.CRON,
            cron_expression="0 2 * * *",
        )
        schedule_id = await scheduler.add(schedule)

        # Create new scheduler with same DB
        scheduler2 = SchedulerEngine(db, workflow_engine, registry)
        await scheduler2.start()
        await scheduler2.stop()

        sched = await scheduler2.get(schedule_id)
        assert sched is not None
        assert sched["name"] == "persist-test"
        assert sched["schedule_type"] == "cron"
        assert sched["cron_expression"] == "0 2 * * *"
        assert sched["status"] == "pending"

    except Exception as exc:
        pytest.fail(f"Schedule persistence test failed: {exc}\n{traceback.format_exc()}")
    finally:
        if db:
            await db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])