"""Tests for ContractEnforcerLifecycle.

Authority: I2-004 §4.6
"""

import pytest

from sam.runtime.contract_enforcer import (
    ContractEnforcerLifecycle,
    ContractEnforcerLifecycleState,
)


class TestContractEnforcerLifecycleState:
    """Tests for lifecycle state enum."""

    def test_has_five_states(self) -> None:
        """5 states: UNINITIALIZED, INITIALIZING, RUNNING, STOPPING, STOPPED."""
        states = list(ContractEnforcerLifecycleState)
        assert len(states) == 5

    def test_running_is_operational(self) -> None:
        """Only RUNNING is operational."""
        assert ContractEnforcerLifecycleState.RUNNING.is_operational() is True

    def test_uninitialized_not_operational(self) -> None:
        """UNINITIALIZED is not operational."""
        assert ContractEnforcerLifecycleState.UNINITIALIZED.is_operational() is False

    def test_stopped_is_terminal(self) -> None:
        """STOPPED is terminal."""
        assert ContractEnforcerLifecycleState.STOPPED.is_terminal() is True


class TestContractEnforcerLifecycle:
    """Tests for lifecycle state machine."""

    def setup_method(self) -> None:
        self.lc = ContractEnforcerLifecycle()

    def test_initial_state_is_uninitialized(self) -> None:
        """New lifecycle starts at UNINITIALIZED."""
        assert self.lc.state == ContractEnforcerLifecycleState.UNINITIALIZED

    def test_valid_initializing(self) -> None:
        """UNINITIALIZED → INITIALIZING."""
        self.lc.transition_to(ContractEnforcerLifecycleState.INITIALIZING)
        assert self.lc.state == ContractEnforcerLifecycleState.INITIALIZING

    def test_valid_to_running(self) -> None:
        """INITIALIZING → RUNNING."""
        self.lc.transition_to(ContractEnforcerLifecycleState.INITIALIZING)
        self.lc.transition_to(ContractEnforcerLifecycleState.RUNNING)
        assert self.lc.state == ContractEnforcerLifecycleState.RUNNING

    def test_valid_running_to_stopping(self) -> None:
        """RUNNING → STOPPING."""
        self._goto_running()
        self.lc.transition_to(ContractEnforcerLifecycleState.STOPPING)
        assert self.lc.state == ContractEnforcerLifecycleState.STOPPING

    def test_valid_stopping_to_stopped(self) -> None:
        """STOPPING → STOPPED."""
        self._goto_running()
        self.lc.transition_to(ContractEnforcerLifecycleState.STOPPING)
        self.lc.transition_to(ContractEnforcerLifecycleState.STOPPED)
        assert self.lc.state == ContractEnforcerLifecycleState.STOPPED

    def test_invalid_skip_running(self) -> None:
        """UNINITIALIZED → RUNNING (skip) not allowed."""
        with pytest.raises(ValueError, match="Invalid transition"):
            self.lc.transition_to(ContractEnforcerLifecycleState.RUNNING)

    def test_invalid_from_stopped(self) -> None:
        """STOPPED is terminal — no further transitions."""
        self._goto_stopped()
        with pytest.raises(ValueError, match="Invalid transition"):
            self.lc.transition_to(ContractEnforcerLifecycleState.RUNNING)

    def test_same_state_is_noop(self) -> None:
        """Transition to same state is no-op."""
        self.lc.transition_to(ContractEnforcerLifecycleState.UNINITIALIZED)
        assert self.lc.state == ContractEnforcerLifecycleState.UNINITIALIZED

    def test_is_operational(self) -> None:
        """is_operational True only for RUNNING."""
        assert self.lc.is_operational() is False
        self._goto_running()
        assert self.lc.is_operational() is True

    def test_is_terminal(self) -> None:
        """is_terminal True only for STOPPED."""
        assert self.lc.is_terminal() is False
        self._goto_stopped()
        assert self.lc.is_terminal() is True

    def test_full_lifecycle_path(self) -> None:
        """Complete path to STOPPED."""
        path = [
            ContractEnforcerLifecycleState.INITIALIZING,
            ContractEnforcerLifecycleState.RUNNING,
            ContractEnforcerLifecycleState.STOPPING,
            ContractEnforcerLifecycleState.STOPPED,
        ]
        for target in path:
            self.lc.transition_to(target)
        assert self.lc.state == ContractEnforcerLifecycleState.STOPPED
        assert self.lc.is_terminal() is True

    def _goto_running(self) -> None:
        self.lc.transition_to(ContractEnforcerLifecycleState.INITIALIZING)
        self.lc.transition_to(ContractEnforcerLifecycleState.RUNNING)

    def _goto_stopped(self) -> None:
        self._goto_running()
        self.lc.transition_to(ContractEnforcerLifecycleState.STOPPING)
        self.lc.transition_to(ContractEnforcerLifecycleState.STOPPED)
