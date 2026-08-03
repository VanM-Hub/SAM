"""Tests for Capability Manager health service.

Verifies: health status mapping from ManagerLifecycle.

Authority: I2-002 §6.1
"""

from sam.runtime.capability_manager.lifecycle.manager_lifecycle import (
    ManagerLifecycle,
    ManagerLifecycleState,
)
from sam.runtime.capability_manager.services.health_service import (
    HealthService,
)


class TestHealthService:
    """Tests for HealthService."""

    def setup_method(self) -> None:
        self.lifecycle = ManagerLifecycle()
        self.service = HealthService(lifecycle=self.lifecycle)

    def test_uninitialized_is_unavailable(self) -> None:
        """UNINITIALIZED reports 'unavailable'."""
        assert self.service.get_health() == "unavailable"

    def test_initializing_is_degraded(self) -> None:
        """INITIALIZING reports 'degraded'."""
        self.lifecycle.transition_to(ManagerLifecycleState.INITIALIZING)
        assert self.service.get_health() == "degraded"

    def test_running_is_available(self) -> None:
        """RUNNING reports 'available'."""
        self.lifecycle.transition_to(ManagerLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(ManagerLifecycleState.RUNNING)
        assert self.service.get_health() == "available"

    def test_stopping_is_degraded(self) -> None:
        """STOPPING reports 'degraded'."""
        self.lifecycle.transition_to(ManagerLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(ManagerLifecycleState.RUNNING)
        self.lifecycle.transition_to(ManagerLifecycleState.STOPPING)
        assert self.service.get_health() == "degraded"

    def test_stopped_is_unavailable(self) -> None:
        """STOPPED reports 'unavailable'."""
        self.lifecycle.transition_to(ManagerLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(ManagerLifecycleState.RUNNING)
        self.lifecycle.transition_to(ManagerLifecycleState.STOPPING)
        self.lifecycle.transition_to(ManagerLifecycleState.STOPPED)
        assert self.service.get_health() == "unavailable"
