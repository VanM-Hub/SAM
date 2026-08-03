"""Tests: Scheduler Lifecycle — 5-state lifecycle."""

import pytest
from src.sam.runtime.execution_scheduler.lifecycle.scheduler_lifecycle import (
    SchedulerLifecycle,
    SchedulerLifecycleState,
    is_operational,
    is_terminal,
    is_valid_scheduler_transition,
)


class TestSchedulerLifecycleState:
    def test_has_five_states(self):
        states = list(SchedulerLifecycleState)
        assert len(states) == 5

    def test_running_is_operational(self):
        assert is_operational(SchedulerLifecycleState.RUNNING) is True

    def test_uninitialized_not_operational(self):
        assert is_operational(SchedulerLifecycleState.UNINITIALIZED) is False

    def test_stopped_is_terminal(self):
        assert is_terminal(SchedulerLifecycleState.STOPPED) is True

    def test_stopped_not_operational(self):
        assert is_operational(SchedulerLifecycleState.STOPPED) is False


class TestSchedulerLifecycleTransitions:
    def test_initial_state_is_uninitialized(self):
        lc = SchedulerLifecycle()
        assert lc.state == SchedulerLifecycleState.UNINITIALIZED

    def test_valid_uninitialized_to_initializing(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        assert lc.state == SchedulerLifecycleState.INITIALIZING

    def test_valid_initializing_to_running(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        assert lc.state == SchedulerLifecycleState.RUNNING

    def test_valid_running_to_stopping(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        lc.transition(SchedulerLifecycleState.STOPPING)
        assert lc.state == SchedulerLifecycleState.STOPPING

    def test_valid_stopping_to_stopped(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        lc.transition(SchedulerLifecycleState.STOPPING)
        lc.transition(SchedulerLifecycleState.STOPPED)
        assert lc.state == SchedulerLifecycleState.STOPPED

    def test_invalid_skip_initializing(self):
        lc = SchedulerLifecycle()
        with pytest.raises(ValueError, match="Invalid scheduler transition"):
            lc.transition(SchedulerLifecycleState.RUNNING)

    def test_invalid_from_stopped(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        lc.transition(SchedulerLifecycleState.STOPPING)
        lc.transition(SchedulerLifecycleState.STOPPED)
        with pytest.raises(ValueError):
            lc.transition(SchedulerLifecycleState.RUNNING)

    def test_same_state_is_noop(self):
        lc = SchedulerLifecycle()
        lc.transition(SchedulerLifecycleState.UNINITIALIZED)  # no-op
        assert lc.state == SchedulerLifecycleState.UNINITIALIZED

    def test_is_operational(self):
        lc = SchedulerLifecycle()
        assert lc.is_operational() is False
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        assert lc.is_operational() is True

    def test_is_terminal(self):
        lc = SchedulerLifecycle()
        assert lc.is_terminal() is False
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        lc.transition(SchedulerLifecycleState.STOPPING)
        lc.transition(SchedulerLifecycleState.STOPPED)
        assert lc.is_terminal() is True

    def test_full_lifecycle_path(self):
        lc = SchedulerLifecycle()
        states = list(SchedulerLifecycleState)
        # UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED
        lc.transition(SchedulerLifecycleState.INITIALIZING)
        lc.transition(SchedulerLifecycleState.RUNNING)
        lc.transition(SchedulerLifecycleState.STOPPING)
        lc.transition(SchedulerLifecycleState.STOPPED)
        assert lc.is_terminal() is True

    def test_repr(self):
        lc = SchedulerLifecycle()
        r = repr(lc)
        assert "UNINITIALIZED" in r

    def test_is_valid_transition_function(self):
        assert is_valid_scheduler_transition(
            SchedulerLifecycleState.UNINITIALIZED,
            SchedulerLifecycleState.INITIALIZING,
        ) is True
        assert is_valid_scheduler_transition(
            SchedulerLifecycleState.UNINITIALIZED,
            SchedulerLifecycleState.RUNNING,
        ) is False

    def test_uninitialized_to_stopping_invalid(self):
        lc = SchedulerLifecycle()
        with pytest.raises(ValueError):
            lc.transition(SchedulerLifecycleState.STOPPING)
