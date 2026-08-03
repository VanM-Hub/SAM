"""Tests: Health service mapping."""

from src.sam.runtime.approval_coordinator.lifecycle.coordinator_lifecycle import (
    ApprovalCoordinatorLifecycle,
    CoordinatorLifecycleState,
)
from src.sam.runtime.approval_coordinator.services.health_service import (
    HealthService,
    HealthStatus,
)


class TestHealthService:
    """Tests for HealthService."""

    def test_uninitialized_is_unavailable(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        health = HealthService.get_health(lifecycle)
        assert health["status"] == HealthStatus.UNAVAILABLE.value

    def test_initializing_is_degraded(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.INITIALIZING
        health = HealthService.get_health(lifecycle)
        assert health["status"] == HealthStatus.DEGRADED.value

    def test_running_is_available(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.RUNNING
        health = HealthService.get_health(lifecycle)
        assert health["status"] == HealthStatus.AVAILABLE.value

    def test_stopping_is_degraded(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.STOPPING
        health = HealthService.get_health(lifecycle)
        assert health["status"] == HealthStatus.DEGRADED.value

    def test_stopped_is_unavailable(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.STOPPED
        health = HealthService.get_health(lifecycle)
        assert health["status"] == HealthStatus.UNAVAILABLE.value

    def test_health_includes_lifecycle_state(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.RUNNING
        health = HealthService.get_health(lifecycle)
        assert health["lifecycle_state"] == "RUNNING"

    def test_health_includes_operational_flag(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.RUNNING
        health = HealthService.get_health(lifecycle)
        assert health["operational"] is True

    def test_health_includes_terminal_flag(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.STOPPED
        health = HealthService.get_health(lifecycle)
        assert health["terminal"] is True
