"""Test RecorderLifecycle transitions.

Per I2-007 package spec: UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED
"""

import pytest
from src.sam.runtime.audit_recorder.lifecycle.recorder_lifecycle import (
    RecorderLifecycleState,
    LEGAL_RECORDER_TRANSITIONS,
    is_legal_recorder_transition,
)


class TestRecorderLifecycle:
    """Verify recorder-level lifecycle state machine."""

    def test_five_states_defined(self):
        """Exactly 5 recorder lifecycle states."""
        states = list(RecorderLifecycleState)
        assert len(states) == 5

    def test_initial_to_initializing(self):
        """UNINITIALIZED → INITIALIZING."""
        assert is_legal_recorder_transition(
            RecorderLifecycleState.UNINITIALIZED,
            RecorderLifecycleState.INITIALIZING,
        )

    def test_initializing_to_running(self):
        """INITIALIZING → RUNNING."""
        assert is_legal_recorder_transition(
            RecorderLifecycleState.INITIALIZING,
            RecorderLifecycleState.RUNNING,
        )

    def test_initializing_to_stopped(self):
        """INITIALIZING → STOPPED (error path)."""
        assert is_legal_recorder_transition(
            RecorderLifecycleState.INITIALIZING,
            RecorderLifecycleState.STOPPED,
        )

    def test_running_to_stopping(self):
        """RUNNING → STOPPING."""
        assert is_legal_recorder_transition(
            RecorderLifecycleState.RUNNING,
            RecorderLifecycleState.STOPPING,
        )

    def test_stopping_to_stopped(self):
        """STOPPING → STOPPED."""
        assert is_legal_recorder_transition(
            RecorderLifecycleState.STOPPING,
            RecorderLifecycleState.STOPPED,
        )

    def test_stopped_is_terminal(self):
        """STOPPED is terminal."""
        assert RecorderLifecycleState.STOPPED.is_terminal is True
        assert RecorderLifecycleState.RUNNING.is_terminal is False

    def test_illegal_transitions(self):
        """Verify illegal transitions are rejected."""
        illegal_pairs = [
            (RecorderLifecycleState.UNINITIALIZED, RecorderLifecycleState.RUNNING),
            (RecorderLifecycleState.RUNNING, RecorderLifecycleState.UNINITIALIZED),
            (RecorderLifecycleState.STOPPED, RecorderLifecycleState.RUNNING),
            (RecorderLifecycleState.STOPPED, RecorderLifecycleState.UNINITIALIZED),
        ]
        for current, target in illegal_pairs:
            assert not is_legal_recorder_transition(current, target), (
                f"Should be illegal: {current.value} → {target.value}"
            )

    def test_initialize_shutdown_flow(self):
        """Normal flow: UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED."""
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )
        s = RecorderService()
        assert s.lifecycle_state == RecorderLifecycleState.UNINITIALIZED

        s.initialize()
        assert s.lifecycle_state == RecorderLifecycleState.RUNNING

        s.shutdown()
        assert s.lifecycle_state == RecorderLifecycleState.STOPPED

    def test_illegal_transition_raises_error(self):
        """Illegal transition raises ValueError."""
        from src.sam.runtime.audit_recorder.services.recorder_service import (
            RecorderService,
        )
        s = RecorderService()
        # Cannot jump directly from UNINITIALIZED to RUNNING
        # (initialize does it in two steps, but _transition_lifecycle enforces)
        with pytest.raises(ValueError, match="Illegal"):
            s._transition_lifecycle(RecorderLifecycleState.RUNNING)
