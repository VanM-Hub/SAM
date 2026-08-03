"""Tests: ApprovalCoordinatorLifecycle state machine."""

import pytest

from src.sam.runtime.approval_coordinator.lifecycle.coordinator_lifecycle import (
    ApprovalCoordinatorLifecycle,
    CoordinatorLifecycleState,
)


class TestCoordinatorLifecycleState:
    """Tests for the lifecycle state enum."""

    def test_has_five_states(self):
        states = list(CoordinatorLifecycleState)
        assert len(states) == 5

    def test_running_is_operational(self):
        """RUNNING should be marked as operational state."""
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.RUNNING
        assert lifecycle.is_operational() is True

    def test_uninitialized_not_operational(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        assert lifecycle.is_operational() is False

    def test_stopped_is_terminal(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.STOPPED
        assert lifecycle.is_terminal() is True


class TestCoordinatorLifecycleTransitions:
    """Tests for lifecycle transitions."""

    def test_initial_state_is_uninitialized(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        assert lifecycle.state == CoordinatorLifecycleState.UNINITIALIZED

    def test_valid_uninitialized_to_initializing(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle.transition(CoordinatorLifecycleState.INITIALIZING)
        assert lifecycle.state == CoordinatorLifecycleState.INITIALIZING

    def test_valid_initializing_to_running(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.INITIALIZING
        lifecycle.transition(CoordinatorLifecycleState.RUNNING)
        assert lifecycle.state == CoordinatorLifecycleState.RUNNING

    def test_valid_running_to_stopping(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.RUNNING
        lifecycle.transition(CoordinatorLifecycleState.STOPPING)
        assert lifecycle.state == CoordinatorLifecycleState.STOPPING

    def test_valid_stopping_to_stopped(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.STOPPING
        lifecycle.transition(CoordinatorLifecycleState.STOPPED)
        assert lifecycle.state == CoordinatorLifecycleState.STOPPED

    def test_invalid_skip_initializing(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        with pytest.raises(ValueError, match="Invalid lifecycle transition"):
            lifecycle.transition(CoordinatorLifecycleState.RUNNING)

    def test_invalid_from_stopped(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.STOPPED
        with pytest.raises(ValueError):
            lifecycle.transition(CoordinatorLifecycleState.RUNNING)

    def test_same_state_is_noop(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle.transition(CoordinatorLifecycleState.UNINITIALIZED)
        assert lifecycle.state == CoordinatorLifecycleState.UNINITIALIZED

    def test_is_operational(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        assert lifecycle.is_operational() is False
        lifecycle._state = CoordinatorLifecycleState.RUNNING
        assert lifecycle.is_operational() is True
        lifecycle._state = CoordinatorLifecycleState.STOPPING
        assert lifecycle.is_operational() is False

    def test_is_terminal(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        assert lifecycle.is_terminal() is False
        lifecycle._state = CoordinatorLifecycleState.STOPPED
        assert lifecycle.is_terminal() is True

    def test_full_lifecycle_path(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        assert lifecycle.state == CoordinatorLifecycleState.UNINITIALIZED

        lifecycle.transition(CoordinatorLifecycleState.INITIALIZING)
        assert lifecycle.state == CoordinatorLifecycleState.INITIALIZING

        lifecycle.transition(CoordinatorLifecycleState.RUNNING)
        assert lifecycle.state == CoordinatorLifecycleState.RUNNING
        assert lifecycle.is_operational()

        lifecycle.transition(CoordinatorLifecycleState.STOPPING)
        assert lifecycle.state == CoordinatorLifecycleState.STOPPING
        assert not lifecycle.is_operational()

        lifecycle.transition(CoordinatorLifecycleState.STOPPED)
        assert lifecycle.state == CoordinatorLifecycleState.STOPPED
        assert lifecycle.is_terminal()

    def test_repr(self):
        lifecycle = ApprovalCoordinatorLifecycle()
        lifecycle._state = CoordinatorLifecycleState.RUNNING
        r = repr(lifecycle)
        assert "RUNNING" in r
