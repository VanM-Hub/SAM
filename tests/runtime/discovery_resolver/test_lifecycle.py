"""Tests for ResolverLifecycle state machine.

Authority: I2-003 §4
"""

import pytest

from sam.runtime.discovery_resolver import (
    ResolverLifecycle,
    ResolverLifecycleState,
)


class TestResolverLifecycleState:
    """Tests for ResolverLifecycleState enum."""

    def test_has_five_states(self) -> None:
        """ResolverLifecycleState has exactly 5 states."""
        states = list(ResolverLifecycleState)
        assert len(states) == 5

    def test_uninitialized_is_initial(self) -> None:
        """UNINITIALIZED exists and is not operational or terminal."""
        assert ResolverLifecycleState.UNINITIALIZED.is_operational() is False
        assert ResolverLifecycleState.UNINITIALIZED.is_terminal() is False

    def test_running_is_operational(self) -> None:
        """RUNNING is the only operational state."""
        assert ResolverLifecycleState.RUNNING.is_operational() is True
        assert ResolverLifecycleState.RUNNING.is_terminal() is False

    def test_stopped_is_terminal(self) -> None:
        """STOPPED is the only terminal state."""
        assert ResolverLifecycleState.STOPPED.is_terminal() is True
        assert ResolverLifecycleState.STOPPED.is_operational() is False


class TestResolverLifecycle:
    """Tests for ResolverLifecycle state machine."""

    def setup_method(self) -> None:
        self.lc = ResolverLifecycle()

    def test_initial_state_is_uninitialized(self) -> None:
        """New lifecycle starts at UNINITIALIZED."""
        assert self.lc.state == ResolverLifecycleState.UNINITIALIZED

    def test_valid_initializing(self) -> None:
        """UNINITIALIZED → INITIALIZING is allowed."""
        self.lc.transition_to(ResolverLifecycleState.INITIALIZING)
        assert self.lc.state == ResolverLifecycleState.INITIALIZING

    def test_valid_initializing_to_running(self) -> None:
        """INITIALIZING → RUNNING is allowed."""
        self.lc.transition_to(ResolverLifecycleState.INITIALIZING)
        self.lc.transition_to(ResolverLifecycleState.RUNNING)
        assert self.lc.state == ResolverLifecycleState.RUNNING

    def test_valid_running_to_stopping(self) -> None:
        """RUNNING → STOPPING is allowed."""
        self._goto_running()
        self.lc.transition_to(ResolverLifecycleState.STOPPING)
        assert self.lc.state == ResolverLifecycleState.STOPPING

    def test_valid_stopping_to_stopped(self) -> None:
        """STOPPING → STOPPED is allowed."""
        self._goto_running()
        self.lc.transition_to(ResolverLifecycleState.STOPPING)
        self.lc.transition_to(ResolverLifecycleState.STOPPED)
        assert self.lc.state == ResolverLifecycleState.STOPPED

    def test_invalid_uninitialized_to_running(self) -> None:
        """UNINITIALIZED → RUNNING (skip) is NOT allowed."""
        with pytest.raises(ValueError, match="Invalid transition"):
            self.lc.transition_to(ResolverLifecycleState.RUNNING)

    def test_invalid_from_stopped(self) -> None:
        """STOPPED is terminal — no transitions."""
        self._goto_stopped()
        with pytest.raises(ValueError, match="Invalid transition"):
            self.lc.transition_to(ResolverLifecycleState.RUNNING)

    def test_same_state_is_noop(self) -> None:
        """Transition to same state is a no-op."""
        self.lc.transition_to(ResolverLifecycleState.UNINITIALIZED)
        assert self.lc.state == ResolverLifecycleState.UNINITIALIZED

    def test_is_operational(self) -> None:
        """is_operational returns True only for RUNNING."""
        assert self.lc.is_operational() is False
        self._goto_running()
        assert self.lc.is_operational() is True

    def test_is_terminal(self) -> None:
        """is_terminal returns True only for STOPPED."""
        assert self.lc.is_terminal() is False
        self._goto_stopped()
        assert self.lc.is_terminal() is True

    def test_complete_lifecycle_path(self) -> None:
        """Full path: UNINITIALIZED → ... → STOPPED."""
        path = [
            ResolverLifecycleState.INITIALIZING,
            ResolverLifecycleState.RUNNING,
            ResolverLifecycleState.STOPPING,
            ResolverLifecycleState.STOPPED,
        ]
        for target in path:
            self.lc.transition_to(target)
        assert self.lc.state == ResolverLifecycleState.STOPPED
        assert self.lc.is_terminal() is True

    # ── Helpers ──────────────────────────────────────────────────

    def _goto_running(self) -> None:
        self.lc.transition_to(ResolverLifecycleState.INITIALIZING)
        self.lc.transition_to(ResolverLifecycleState.RUNNING)

    def _goto_stopped(self) -> None:
        self.lc.transition_to(ResolverLifecycleState.INITIALIZING)
        self.lc.transition_to(ResolverLifecycleState.RUNNING)
        self.lc.transition_to(ResolverLifecycleState.STOPPING)
        self.lc.transition_to(ResolverLifecycleState.STOPPED)
