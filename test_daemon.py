"""
Test RuntimeDaemon – Fase 8 Sprint 15

Tests:
1. Start -> stop -> health
2. Health aggregation with multiple services
3. Graceful shutdown timeout
4. Double start/stop idempotency
5. Signal handling (simulated via _handle_signal)
6. Run forever with stop
"""

import asyncio
import pytest
import signal
from typing import Optional, Dict, Any

from src.sam.core.daemon import RuntimeDaemon, DaemonConfig
from src.sam.core.service import RuntimeService
from src.sam.core.event_bus import EventBus
from src.sam.core.clock import SystemClock, FrozenClock, VirtualClock
from src.sam.core.health import ServiceHealth, HealthStatus
from src.sam.core.events import ServiceStarted, ServiceStopped, ServiceHealthChanged


# ── Helper Services ──────────────────────────────────────────────

class DummyService(RuntimeService):
    """Simple test service with controllable health."""

    def __init__(self, name: str = "dummy", fail_on_start: bool = False):
        super().__init__()
        self._name = name
        self._fail_on_start = fail_on_start
        self._health_status = HealthStatus.HEALTHY
        self._health_message = "OK"
        self.initialize_called = False
        self.start_called = False
        self.stop_called = False

    @property
    def name(self) -> str:
        return self._name

    async def initialize(self) -> None:
        self.initialize_called = True
        self._initialized = True

    async def start(self) -> None:
        if self._fail_on_start:
            raise RuntimeError(f"{self._name} start failed")
        self.start_called = True
        self._started = True

    async def stop(self) -> None:
        self.stop_called = True
        self._started = False

    async def health(self) -> ServiceHealth:
        return ServiceHealth(
            status=self._health_status,
            message=self._health_message,
            metrics={"name": self._name},
            last_check=__import__("datetime").datetime.utcnow(),
        )

    def set_health(self, status: HealthStatus, message: str = "") -> None:
        self._health_status = status
        self._health_message = message


class SlowStopService(RuntimeService):
    """Service that takes time to stop (tests shutdown timeout)."""

    def __init__(self, name: str = "slow_stop", stop_delay: float = 0.5):
        super().__init__()
        self._name = name
        self._stop_delay = stop_delay

    @property
    def name(self) -> str:
        return self._name

    async def initialize(self) -> None:
        self._initialized = True

    async def start(self) -> None:
        self._started = True

    async def stop(self) -> None:
        await asyncio.sleep(self._stop_delay)
        self._started = False

    async def health(self) -> ServiceHealth:
        return ServiceHealth.healthy(self._name)


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def dummy_service():
    return DummyService(name="test_dummy")


@pytest.fixture
async def daemon(event_bus, dummy_service):
    config = DaemonConfig(
        health_check_interval=9999,  # Don't run health check in tests
        shutdown_timeout=5.0,
    )
    d = RuntimeDaemon(
        config=config,
        event_bus=event_bus,
        services=[dummy_service],
    )
    yield d
    # Cleanup: stop if running
    if d.running:
        await d.stop()


# ── 1. Start -> Stop -> Health ───────────────────────────────────

@pytest.mark.asyncio
async def test_start_stop(daemon, dummy_service):
    """Start daemon, verify service started, then stop."""
    assert not daemon.running
    assert not dummy_service.initialize_called
    assert not dummy_service.start_called

    await daemon.start()
    assert daemon.running
    assert dummy_service.initialize_called
    assert dummy_service.start_called

    # Check health
    health = await daemon.health()
    assert "daemon" in health
    assert "test_dummy" in health
    assert health["daemon"].status == HealthStatus.HEALTHY
    assert health["test_dummy"].status == HealthStatus.HEALTHY

    await daemon.stop()
    assert not daemon.running
    assert dummy_service.stop_called


@pytest.mark.asyncio
async def test_health_when_not_running():
    """Health should show UNHEALTHY when daemon not started."""
    d = RuntimeDaemon()
    health = await d.health()
    assert "daemon" in health
    assert health["daemon"].status == HealthStatus.UNHEALTHY
    assert "not running" in health["daemon"].message


# ── 2. Health Aggregation ────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_aggregation(event_bus):
    """Health should aggregate status from all services."""
    svc1 = DummyService(name="healthy_svc")
    svc2 = DummyService(name="degraded_svc")
    svc2.set_health(HealthStatus.DEGRADED, "something wrong")

    config = DaemonConfig(health_check_interval=9999)
    d = RuntimeDaemon(config=config, event_bus=event_bus, services=[svc1, svc2])

    await d.start()

    health = await d.health()
    assert health["healthy_svc"].status == HealthStatus.HEALTHY
    assert health["degraded_svc"].status == HealthStatus.DEGRADED
    # Daemon overall should be DEGRADED (not UNHEALTHY)
    assert health["daemon"].status == HealthStatus.DEGRADED

    await d.stop()


@pytest.mark.asyncio
async def test_health_aggregation_unhealthy(event_bus):
    """Unhealthy service should make daemon UNHEALTHY overall."""
    svc = DummyService(name="bad_svc")
    svc.set_health(HealthStatus.UNHEALTHY, "crashed")

    config = DaemonConfig(health_check_interval=9999)
    d = RuntimeDaemon(config=config, event_bus=event_bus, services=[svc])

    await d.start()

    health = await d.health()
    assert health["bad_svc"].status == HealthStatus.UNHEALTHY
    assert health["daemon"].status == HealthStatus.UNHEALTHY

    await d.stop()


# ── 3. Graceful Shutdown ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_graceful_shutdown(event_bus):
    """Stop with slow services should complete within timeout."""
    slow = SlowStopService(name="slow", stop_delay=0.3)
    fast = DummyService(name="fast")

    config = DaemonConfig(health_check_interval=9999, shutdown_timeout=5.0)
    d = RuntimeDaemon(config=config, event_bus=event_bus, services=[fast, slow])

    await d.start()
    assert d.running

    # Stop should handle slow services
    await d.stop()
    assert not d.running
    assert fast.stop_called
    assert not fast._started
    assert not slow._started


@pytest.mark.asyncio
async def test_shutdown_timeout(event_bus):
    """Shutdown should timeout gracefully without hanging."""
    very_slow = SlowStopService(name="very_slow", stop_delay=10.0)

    config = DaemonConfig(
        health_check_interval=9999,
        shutdown_timeout=0.5,  # Very short timeout
    )
    d = RuntimeDaemon(config=config, event_bus=event_bus, services=[very_slow])

    await d.start()
    start = __import__("time").time()
    await d.stop()
    elapsed = __import__("time").time() - start

    # Should complete within reasonable time (a bit over 0.5s due to asyncio overhead)
    assert elapsed < 3.0, f"Shutdown took too long: {elapsed:.2f}s"
    assert not d.running


# ── 4. Double Start/Stop ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_double_start(daemon):
    """Calling start twice should be idempotent."""
    await daemon.start()
    await daemon.start()  # Second start should be no-op
    assert daemon.running


@pytest.mark.asyncio
async def test_double_stop(daemon):
    """Calling stop twice should be idempotent."""
    await daemon.start()
    await daemon.stop()
    await daemon.stop()  # Second stop should be no-op
    assert not daemon.running


# ── 5. Signal Handling ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_signal_handling(event_bus):
    """Simulate signal handling triggers shutdown."""
    config = DaemonConfig(health_check_interval=9999)
    d = RuntimeDaemon(config=config, event_bus=event_bus, services=[DummyService()])

    await d.start()
    assert d.running

    # Simulate SIGTERM
    await d._handle_signal(signal.SIGTERM)

    # After _handle_signal, the shutdown_event is set but stop() wasn't called yet
    # In run_forever, it would wait for the event then call stop()
    # Here we directly verify the event is set
    assert d._shutdown_event.is_set()

    # Manually stop
    await d.stop()
    assert not d.running


# ── 6. Run Forever ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_forever_stop(event_bus):
    """run_forever should start and be stoppable via shutdown event."""
    config = DaemonConfig(health_check_interval=9999)
    d = RuntimeDaemon(config=config, event_bus=event_bus, services=[DummyService()])

    # Start the run_forever loop in a task
    task = asyncio.create_task(d.run_forever())

    # Give it a moment to start
    await asyncio.sleep(0.2)

    # Signal shutdown
    d._shutdown_event.set()

    # Wait for task to complete
    await asyncio.wait_for(task, timeout=5.0)

    assert not d.running


# ── 7. Add Service After Construction ────────────────────────────

@pytest.mark.asyncio
async def test_add_service_after_construction(event_bus):
    """Services can be added after daemon construction."""
    config = DaemonConfig(health_check_interval=9999)
    d = RuntimeDaemon(config=config, event_bus=event_bus)
    extra = DummyService(name="extra")
    d.add_service(extra)

    assert extra in d._services
    assert len(d._services) == 1

    await d.start()
    health = await d.health()
    assert "extra" in health
    await d.stop()


# ── 8. Event Bus Integration ─────────────────────────────────────

@pytest.mark.asyncio
async def test_event_bus_integration(event_bus):
    """Daemon should publish start/stop events."""
    received = []

    async def collector(event):
        received.append(event.type)

    event_bus.subscribe("service.started", collector)
    event_bus.subscribe("service.stopped", collector)

    config = DaemonConfig(health_check_interval=9999)
    d = RuntimeDaemon(config=config, event_bus=event_bus, services=[DummyService()])

    await d.start()
    await asyncio.sleep(0.1)
    await d.stop()

    # Should have received at least service.started
    assert "service.started" in received


# ── 9. Distributor Integration ───────────────────────────────────


class _MockDistributor:
    """Mock distributor untuk test integrasi daemon."""

    def __init__(self):
        self.distribute_jobs_calls = 0
        self.distribute_workflows_calls = 0
        self._error_on_call: Optional[int] = None
        self._call_count = 0

    async def distribute_jobs(self):
        self._call_count += 1
        self.distribute_jobs_calls += 1
        if self._error_on_call is not None and self._call_count == self._error_on_call:
            raise RuntimeError("distribute_jobs error")

    async def distribute_workflows(self):
        self.distribute_workflows_calls += 1


@pytest.mark.asyncio
async def test_distribution_loop_runs_when_leader(event_bus):
    """Distribution loop starts when daemon is leader with distributor configured."""
    distributor = _MockDistributor()

    config = DaemonConfig(
        health_check_interval=9999,
        distribution_interval=0.1,  # fast poll for test
        try_become_leader=False,  # we'll inject leader state manually
        enable_distribution=True,
    )
    d = RuntimeDaemon(
        config=config,
        event_bus=event_bus,
        distributor=distributor,
        services=[DummyService()],
    )

    await d.start()

    # Inject leader state manually (bypassing actual LeaderElection)
    d._is_leader = True
    d._distributor = distributor
    d._distribution_task = asyncio.create_task(d._distribution_loop())

    # Wait for at least 2 distribution cycles
    await asyncio.sleep(0.35)

    assert distributor.distribute_jobs_calls >= 2
    assert distributor.distribute_workflows_calls >= 2

    await d.stop()


@pytest.mark.asyncio
async def test_distribution_skipped_when_not_leader(event_bus):
    """Distribution loop should not call distribute when node is not leader."""
    distributor = _MockDistributor()

    config = DaemonConfig(
        health_check_interval=9999,
        distribution_interval=0.1,
        enable_distribution=True,
    )
    d = RuntimeDaemon(
        config=config,
        event_bus=event_bus,
        distributor=distributor,
        services=[DummyService()],
    )

    await d.start()

    # Inject non-leader state
    d._is_leader = False
    d._distributor = distributor
    d._distribution_task = asyncio.create_task(d._distribution_loop())

    # Wait long enough that a cycle would have run
    await asyncio.sleep(0.35)

    # Distribution should not have been called
    assert distributor.distribute_jobs_calls == 0
    assert distributor.distribute_workflows_calls == 0

    await d.stop()


@pytest.mark.asyncio
async def test_distribution_skipped_when_disabled(event_bus):
    """Distribution loop does not start when enable_distribution=False."""
    distributor = _MockDistributor()

    config = DaemonConfig(
        health_check_interval=9999,
        enable_distribution=False,
    )
    d = RuntimeDaemon(
        config=config,
        event_bus=event_bus,
        distributor=distributor,
        services=[DummyService()],
    )

    await d.start()
    # Even if leader, task won't be created because enable_distribution is False
    d._is_leader = True

    assert d._distribution_task is None, "Distribution task should not be created when disabled"

    await d.stop()


@pytest.mark.asyncio
async def test_distribution_no_distributor_no_task(event_bus):
    """No distribution task created when distributor is None."""
    config = DaemonConfig(
        health_check_interval=9999,
        enable_distribution=True,
    )
    d = RuntimeDaemon(
        config=config,
        event_bus=event_bus,
        distributor=None,
        services=[DummyService()],
    )

    await d.start()
    d._is_leader = True

    assert d._distribution_task is None, "Distribution task should not be created without distributor"

    await d.stop()


@pytest.mark.asyncio
async def test_distribution_loop_survives_error(event_bus):
    """Distribution loop should continue running after an error in distribute_jobs."""
    distributor = _MockDistributor()
    distributor._error_on_call = 1  # fail first call only

    config = DaemonConfig(
        health_check_interval=9999,
        distribution_interval=0.1,
        enable_distribution=True,
    )
    d = RuntimeDaemon(
        config=config,
        event_bus=event_bus,
        distributor=distributor,
        services=[DummyService()],
    )

    await d.start()
    d._is_leader = True
    d._distribution_task = asyncio.create_task(d._distribution_loop())

    await asyncio.sleep(0.35)

    # Should have at least gotten past the error and made more calls
    assert distributor.distribute_jobs_calls >= 2, f"Expected >=2 calls, got {distributor.distribute_jobs_calls}"

    await d.stop()


# ── 10. Execution Engine Integration ─────────────────────────────


class _MockExecutionEngine:
    """Mock execution engine untuk test integrasi daemon."""

    def __init__(self):
        self._active_graphs: Dict[str, Any] = {}
        self._paused_graphs: set = set()


@pytest.mark.asyncio
async def test_health_includes_execution_engine(event_bus):
    """Health should report execution engine status when configured."""
    engine = _MockExecutionEngine()
    engine._active_graphs = {"g1": "mock", "g2": "mock"}
    engine._paused_graphs = {"g1"}

    config = DaemonConfig(
        health_check_interval=9999,
        enable_execution_engine=True,
    )
    d = RuntimeDaemon(
        config=config,
        event_bus=event_bus,
        services=[DummyService()],
        execution_engine=engine,
    )

    await d.start()
    health = await d.health()

    assert "execution_engine" in health
    assert health["execution_engine"].status == HealthStatus.HEALTHY
    assert "2 active" in health["execution_engine"].message
    assert "1 paused" in health["execution_engine"].message
    assert health["execution_engine"].metrics["active_graphs"] == 2
    assert health["execution_engine"].metrics["paused_graphs"] == 1

    await d.stop()


@pytest.mark.asyncio
async def test_health_skips_engine_when_disabled(event_bus):
    """Health should NOT include execution engine when enable_execution_engine=False."""
    engine = _MockExecutionEngine()
    engine._active_graphs = {"g1": "mock"}

    config = DaemonConfig(
        health_check_interval=9999,
        enable_execution_engine=False,
    )
    d = RuntimeDaemon(
        config=config,
        event_bus=event_bus,
        services=[DummyService()],
        execution_engine=engine,
    )

    await d.start()
    health = await d.health()
    assert "execution_engine" not in health
    await d.stop()


@pytest.mark.asyncio
async def test_health_no_engine_when_none(event_bus):
    """Health should NOT include execution engine when engine is None."""
    config = DaemonConfig(
        health_check_interval=9999,
        enable_execution_engine=True,
    )
    d = RuntimeDaemon(
        config=config,
        event_bus=event_bus,
        services=[DummyService()],
        execution_engine=None,
    )

    await d.start()
    health = await d.health()
    assert "execution_engine" not in health
    await d.stop()


@pytest.mark.asyncio
async def test_execution_engine_property(event_bus):
    """Daemon should expose execution_engine via property."""
    engine = _MockExecutionEngine()
    d = RuntimeDaemon(
        execution_engine=engine,
        event_bus=event_bus,
    )
    assert d.execution_engine is engine


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
