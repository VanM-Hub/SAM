"""Audit Recorder lifecycle states.

Recorder-level lifecycle (not per-record):
- UNINITIALIZED
- INITIALIZING
- RUNNING
- STOPPING
- STOPPED
"""

from enum import Enum
from typing import Dict, Set


class RecorderLifecycleState(str, Enum):
    """Audit Recorder-level lifecycle states."""
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"

    @property
    def is_active(self) -> bool:
        """Return True if the recorder is in an active state."""
        return self == RecorderLifecycleState.RUNNING

    @property
    def is_terminal(self) -> bool:
        """Return True if this state is terminal."""
        return self == RecorderLifecycleState.STOPPED


LEGAL_RECORDER_TRANSITIONS: Dict[
    RecorderLifecycleState, Set[RecorderLifecycleState]
] = {
    RecorderLifecycleState.UNINITIALIZED: {
        RecorderLifecycleState.INITIALIZING,
    },
    RecorderLifecycleState.INITIALIZING: {
        RecorderLifecycleState.RUNNING,
        RecorderLifecycleState.STOPPED,
    },
    RecorderLifecycleState.RUNNING: {
        RecorderLifecycleState.STOPPING,
    },
    RecorderLifecycleState.STOPPING: {
        RecorderLifecycleState.STOPPED,
    },
    RecorderLifecycleState.STOPPED: set(),
}


def is_legal_recorder_transition(
    current: RecorderLifecycleState,
    target: RecorderLifecycleState,
) -> bool:
    """Return True if the recorder lifecycle transition is legal."""
    legal_targets = LEGAL_RECORDER_TRANSITIONS.get(current, set())
    return target in legal_targets
