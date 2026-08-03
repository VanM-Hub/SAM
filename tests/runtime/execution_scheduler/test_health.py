"""Tests: Health Service — maps lifecycle state to health status."""

import pytest
from src.sam.runtime.execution_scheduler.services.scheduler_service import (
    SchedulerService,
)
from src.sam.runtime.execution_scheduler.services.health_service import (
    HealthService,
)
from src.sam.runtime.execution_scheduler.lifecycle.scheduler_lifecycle import (
    SchedulerLifecycle,
    SchedulerLifecycleState,
)


class TestHealthService:
    def test_uninitialized_is_unavailable(self):
        lc = SchedulerLifecycle()
        hs = HealthService(lc)
        health = hs.get_health()
        assert health["status"] == "unavailable"
        assert health["operational"] is False

    def test_initializing_is_degraded(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        hs = HealthService(lc)
        health = hs.get_health()
        assert health["status"] == "degraded"

    def test_running_is_available(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        hs = HealthService(lc)
        health = hs.get_health()
        assert health["status"] == "available"
        assert health["operational"] is True

    def test_stopping_is_degraded(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        lc.transition(SchedulerLifecycleState.STOPPING)
        hs = HealthService(lc)
        health = hs.get_health()
        assert health["status"] == "degraded"

    def test_stopped_is_unavailable(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        lc.transition(SchedulerLifecycleState.STOPPING)
        lc.transition(SchedulerLifecycleState.STOPPED)
        hs = HealthService(lc)
        health = hs.get_health()
        assert health["status"] == "unavailable"
        assert health["operational"] is False

    def test_health_includes_lifecycle_state(self):
        lc = SchedulerLifecycle()
        hs = HealthService(lc)
        health = hs.get_health()
        assert health["lifecycle_state"] == "UNINITIALIZED"

    def test_health_includes_operational_flag(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        hs = HealthService(lc)
        health = hs.get_health()
        assert health["operational"] is True
        assert health["terminal"] is False

    def test_health_includes_terminal_flag(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        lc.transition(SchedulerLifecycleState.STOPPING)
        lc.transition(SchedulerLifecycleState.STOPPED)
        hs = HealthService(lc)
        health = hs.get_health()
        assert health["terminal"] is True

    def test_is_available(self):
        lc = SchedulerLifecycle()
        hs = HealthService(lc)
        assert hs.is_available() is False
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        assert hs.is_available() is True


class TestServiceHealth:
    def test_uninitialized(self):
        svc = SchedulerService()
        health = svc.get_health()
        assert health["status"] == "unavailable"

    def test_after_initialize(self):
        svc = SchedulerService()
        svc.initialize()
        health = svc.get_health()
        assert health["status"] == "available"
        assert health["operational"] is True

    def test_after_shutdown(self):
        svc = SchedulerService()
        svc.initialize()
        svc.shutdown()
        health = svc.get_health()
        assert health["status"] == "unavailable"
        assert health["operational"] is False
        assert health["terminal"] is True
