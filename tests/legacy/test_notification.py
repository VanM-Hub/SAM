import asyncio
import io
import sys as _sys
from datetime import datetime

from src.sam.core.notification import Notification, NotificationSeverity
from src.sam.core.notification_service import NotificationService
from src.sam.core.event_bus import EventBus
from src.sam.core.clock import FrozenClock
from src.sam.core.events import (
    JobFailed,
    JobCompleted,
    PluginInstalled,
    PluginEnabled,
    PluginDisabled,
    PluginUninstalled,
    ServiceHealthChanged,
    HealthCheckCompleted,
)
from src.sam.core.service_manager import ServiceManager
from src.sam.core.health import HealthStatus


async def test_notification_model():
    clk = FrozenClock(datetime(2026, 7, 24, 12, 0, 0))
    n = Notification(
        type="test.type",
        severity=NotificationSeverity.WARNING,
        title="Test Notification",
        message="This is a test",
        source="test",
        timestamp=clk.now(),
    )
    assert n.type == "test.type"
    assert n.severity == NotificationSeverity.WARNING
    assert n.title == "Test Notification"
    assert n.message == "This is a test"
    assert n.source == "test"
    assert n.timestamp == clk.now()

    # Immutability check
    try:
        n.title = "changed"
        assert False, "Should have raised ValidationError"
    except Exception as e:
        assert "frozen_instance" in str(e) or "frozen" in str(e).lower()

    print("test_notification_model: OK")


async def test_service_subscribes_and_creates():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 12, 0, 0))
    ns = NotificationService(bus, clock=clk, console_channel=False)

    await ns.initialize()

    await bus.publish(JobFailed(
        id="e1",
        source="test",
        payload={"job_id": "j1", "error": "timeout"},
    ))
    await asyncio.sleep(0)

    notifications = ns.get_notifications()
    assert len(notifications) == 1
    n = notifications[0]
    assert n.type == "job.failed"
    assert n.severity == NotificationSeverity.ERROR
    assert "j1" in n.message

    print("test_service_subscribes_and_creates: OK")


async def test_multiple_events():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 12, 0, 0))
    ns = NotificationService(bus, clock=clk, console_channel=False)
    await ns.initialize()

    events_to_fire = [
        JobCompleted(id="e1", source="test", payload={"job_id": "j1"}),
        JobFailed(id="e2", source="test", payload={"job_id": "j2", "error": "err"}),
        PluginInstalled(id="e3", source="test", payload={"plugin_id": "p1"}),
        PluginEnabled(id="e4", source="test", payload={"plugin_id": "p1"}),
        PluginDisabled(id="e5", source="test", payload={"plugin_id": "p1"}),
        PluginUninstalled(id="e6", source="test", payload={"plugin_id": "p1"}),
        ServiceHealthChanged(id="e7", source="test", payload={"service_name": "s1", "status": "degraded"}),
        HealthCheckCompleted(id="e8", source="test", payload={"status": "healthy"}),
    ]

    for ev in events_to_fire:
        await bus.publish(ev)

    await asyncio.sleep(0)

    notifications = ns.get_notifications()
    assert len(notifications) == 8

    # Verify severity mappings
    assert [n for n in notifications if n.type == "job.failed"][0].severity == NotificationSeverity.ERROR
    assert [n for n in notifications if n.type == "plugin.disabled"][0].severity == NotificationSeverity.WARNING
    assert [n for n in notifications if n.type == "service.health_changed"][0].severity == NotificationSeverity.WARNING
    assert [n for n in notifications if n.type == "job.completed"][0].severity == NotificationSeverity.INFO

    print("test_multiple_events: OK")


async def test_health():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 12, 0, 0))
    ns = NotificationService(bus, clock=clk, console_channel=False)
    await ns.initialize()

    h = await ns.health()
    assert h.status == HealthStatus.HEALTHY
    assert h.metrics["subscribed"] is True
    assert h.metrics["notifications"] == 0

    print("test_health: OK")


async def test_console_channel():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 12, 0, 0))
    ns = NotificationService(bus, clock=clk, console_channel=True)
    await ns.initialize()

    captured = io.StringIO()
    old_stdout = _sys.stdout
    _sys.stdout = captured

    try:
        await bus.publish(JobFailed(
            id="e1", source="test", payload={"job_id": "j1", "error": "timeout"},
        ))
        await asyncio.sleep(0)

        output = captured.getvalue()
        assert "ERROR" in output
        assert "Job Failed" in output
        assert "timeout" in output
    finally:
        _sys.stdout = old_stdout

    print("test_console_channel: OK")


async def test_integration_with_service_manager():
    bus = EventBus()
    clk = FrozenClock(datetime(2026, 7, 24, 12, 0, 0))
    ns = NotificationService(bus, clock=clk, console_channel=False)
    sm = ServiceManager(event_bus=bus)

    sm.register(ns)
    await sm.initialize_all()
    await sm.start_all()

    await bus.publish(JobFailed(
        id="e1", source="test", payload={"job_id": "j1", "error": "oops"},
    ))
    await asyncio.sleep(0)

    notifications = ns.get_notifications()
    assert len(notifications) == 1

    await sm.stop_all()
    print("test_integration_with_service_manager: OK")


if __name__ == "__main__":
    tests = [
        test_notification_model,
        test_service_subscribes_and_creates,
        test_multiple_events,
        test_health,
        test_console_channel,
        test_integration_with_service_manager,
    ]
    for t in tests:
        try:
            asyncio.run(t())
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"{t.__name__}: FAILED ({e})")
            _sys.exit(1)
    print("ALL PASSED")
    _sys.exit(0)
