"""Tests for health service.

Authority: I2-004 §4.6
"""

from sam.runtime.contract_enforcer import (
    ContractEnforcer,
    ContractEnforcerLifecycleState,
)


class TestHealthService:
    """Tests for health service."""

    def setup_method(self) -> None:
        self.enforcer = ContractEnforcer()

    def test_uninitialized_is_unavailable(self) -> None:
        """UNINITIALIZED → 'unavailable'."""
        assert self.enforcer.get_health() == "unavailable"

    def test_initializing_is_degraded(self) -> None:
        """INITIALIZING → 'degraded'."""
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.INITIALIZING
        )
        assert self.enforcer.get_health() == "degraded"

    def test_running_is_available(self) -> None:
        """RUNNING → 'available'."""
        self._goto_running()
        assert self.enforcer.get_health() == "available"

    def test_stopping_is_degraded(self) -> None:
        """STOPPING → 'degraded'."""
        self._goto_running()
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.STOPPING
        )
        assert self.enforcer.get_health() == "degraded"

    def test_stopped_is_unavailable(self) -> None:
        """STOPPED → 'unavailable'."""
        self._goto_running()
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.STOPPING
        )
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.STOPPED
        )
        assert self.enforcer.get_health() == "unavailable"

    def _goto_running(self) -> None:
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.INITIALIZING
        )
        self.enforcer.lifecycle.transition_to(
            ContractEnforcerLifecycleState.RUNNING
        )
