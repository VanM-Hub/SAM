"""Tests for Citizen Host lifecycle state machine.

Verifies state transitions, allowed/forbidden paths, operational checks.

Authority: I2-001 §6.2 | R5-001 C2
"""

import pytest

from sam.runtime.citizen_host.lifecycle.host_lifecycle import (
    HostLifecycle,
    HostLifecycleState,
)


class TestHostLifecycle:
    """Tests for HostLifecycle state machine."""

    def setup_method(self) -> None:
        """Set up a fresh HostLifecycle for each test."""
        self.lifecycle = HostLifecycle()

    def test_initial_state_is_uninitialized(self) -> None:
        """Host starts in UNINITIALIZED state."""
        assert self.lifecycle.state == HostLifecycleState.UNINITIALIZED

    def test_valid_transition_uninitialized_to_initializing(self) -> None:
        """UNINITIALIZED → INITIALIZING is allowed."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        assert self.lifecycle.state == HostLifecycleState.INITIALIZING

    def test_valid_transition_initializing_to_running(self) -> None:
        """INITIALIZING → RUNNING is allowed."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        assert self.lifecycle.state == HostLifecycleState.RUNNING

    def test_valid_transition_running_to_degraded(self) -> None:
        """RUNNING → DEGRADED is allowed."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        self.lifecycle.transition_to(HostLifecycleState.DEGRADED)
        assert self.lifecycle.state == HostLifecycleState.DEGRADED

    def test_valid_transition_degraded_to_running(self) -> None:
        """DEGRADED → RUNNING (recovery) is allowed."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        self.lifecycle.transition_to(HostLifecycleState.DEGRADED)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        assert self.lifecycle.state == HostLifecycleState.RUNNING

    def test_valid_transition_running_to_stopping(self) -> None:
        """RUNNING → STOPPING is allowed."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        self.lifecycle.transition_to(HostLifecycleState.STOPPING)
        assert self.lifecycle.state == HostLifecycleState.STOPPING

    def test_valid_transition_stopping_to_stopped(self) -> None:
        """STOPPING → STOPPED is allowed."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        self.lifecycle.transition_to(HostLifecycleState.STOPPING)
        self.lifecycle.transition_to(HostLifecycleState.STOPPED)
        assert self.lifecycle.state == HostLifecycleState.STOPPED

    def test_invalid_transition_uninitialized_to_running(self) -> None:
        """UNINITIALIZED → RUNNING is NOT allowed (skip initialization)."""
        with pytest.raises(ValueError, match="Disallowed transition"):
            self.lifecycle.transition_to(HostLifecycleState.RUNNING)

    def test_invalid_transition_stopped_to_running(self) -> None:
        """STOPPED is terminal — no further transitions allowed."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        self.lifecycle.transition_to(HostLifecycleState.STOPPING)
        self.lifecycle.transition_to(HostLifecycleState.STOPPED)
        with pytest.raises(ValueError, match="Disallowed transition"):
            self.lifecycle.transition_to(HostLifecycleState.RUNNING)

    def test_is_operational_when_running(self) -> None:
        """RUNNING state is operational."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        assert self.lifecycle.is_operational() is True

    def test_is_operational_when_degraded(self) -> None:
        """DEGRADED state is still operational."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        self.lifecycle.transition_to(HostLifecycleState.DEGRADED)
        assert self.lifecycle.is_operational() is True

    def test_is_not_operational_when_stopped(self) -> None:
        """STOPPED state is not operational."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        self.lifecycle.transition_to(HostLifecycleState.STOPPING)
        self.lifecycle.transition_to(HostLifecycleState.STOPPED)
        assert self.lifecycle.is_operational() is False

    def test_is_terminal_when_stopped(self) -> None:
        """STOPPED state is terminal."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        self.lifecycle.transition_to(HostLifecycleState.STOPPING)
        self.lifecycle.transition_to(HostLifecycleState.STOPPED)
        assert self.lifecycle.is_terminal() is True

    def test_is_not_terminal_when_running(self) -> None:
        """RUNNING state is not terminal."""
        self.lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self.lifecycle.transition_to(HostLifecycleState.RUNNING)
        assert self.lifecycle.is_terminal() is False

    def test_complete_lifecycle_normal_path(self) -> None:
        """Full lifecycle: UNINITIALIZED → ... → STOPPED."""
        path = [
            HostLifecycleState.INITIALIZING,
            HostLifecycleState.RUNNING,
            HostLifecycleState.STOPPING,
            HostLifecycleState.STOPPED,
        ]
        for state in path:
            self.lifecycle.transition_to(state)
        assert self.lifecycle.state == HostLifecycleState.STOPPED
        assert self.lifecycle.is_terminal() is True
