"""Tests for Citizen Host health service.

Verifies health status computation from lifecycle state.
Deterministic: same state → same health.

Authority: I2-001 §6.2
"""

from sam.runtime.citizen_host.models.health import HealthStatus
from sam.runtime.citizen_host.lifecycle.host_lifecycle import (
    HostLifecycleState,
)
from sam.runtime.citizen_host.services.health_service import HealthService


class TestHealthService:
    """Tests for HealthService."""

    def setup_method(self) -> None:
        """Set up a fresh HealthService for each test."""
        self.service = HealthService()

    def test_running_state_is_available(self) -> None:
        """RUNNING state reports AVAILABLE health."""
        result = self.service.compute_health(HostLifecycleState.RUNNING)
        assert result == HealthStatus.AVAILABLE

    def test_degraded_state_is_degraded(self) -> None:
        """DEGRADED state reports DEGRADED health."""
        result = self.service.compute_health(HostLifecycleState.DEGRADED)
        assert result == HealthStatus.DEGRADED

    def test_uninitialized_state_is_unavailable(self) -> None:
        """UNINITIALIZED state reports UNAVAILABLE health."""
        result = self.service.compute_health(
            HostLifecycleState.UNINITIALIZED
        )
        assert result == HealthStatus.UNAVAILABLE

    def test_stopped_state_is_unavailable(self) -> None:
        """STOPPED state reports UNAVAILABLE health."""
        result = self.service.compute_health(HostLifecycleState.STOPPED)
        assert result == HealthStatus.UNAVAILABLE

    def test_initializing_state_is_degraded(self) -> None:
        """INITIALIZING state reports DEGRADED health."""
        result = self.service.compute_health(
            HostLifecycleState.INITIALIZING
        )
        assert result == HealthStatus.DEGRADED

    def test_stopping_state_is_degraded(self) -> None:
        """STOPPING state reports DEGRADED health."""
        result = self.service.compute_health(HostLifecycleState.STOPPING)
        assert result == HealthStatus.DEGRADED

    def test_same_state_always_same_result(self) -> None:
        """Determinism: same state always returns same health."""
        for _ in range(5):
            result = self.service.compute_health(
                HostLifecycleState.RUNNING
            )
            assert result == HealthStatus.AVAILABLE

    def test_all_states_have_mapping(self) -> None:
        """Every HostLifecycleState maps to a HealthStatus."""
        for state in HostLifecycleState:
            result = self.service.compute_health(state)
            assert isinstance(result, HealthStatus)
