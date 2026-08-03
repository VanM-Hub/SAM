"""Scheduler Lifecycle — 5-state lifecycle for the Execution Scheduler.

UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED
"""

from enum import Enum
from typing import Set


class SchedulerLifecycleState(str, Enum):
    """5-state lifecycle for Execution Scheduler."""
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


SCHEDULER_LEGAL_TRANSITIONS = {
    SchedulerLifecycleState.UNINITIALIZED: {
        SchedulerLifecycleState.INITIALIZING,
    },
    SchedulerLifecycleState.INITIALIZING: {
        SchedulerLifecycleState.RUNNING,
    },
    SchedulerLifecycleState.RUNNING: {
        SchedulerLifecycleState.STOPPING,
    },
    SchedulerLifecycleState.STOPPING: {
        SchedulerLifecycleState.STOPPED,
    },
    SchedulerLifecycleState.STOPPED: set(),
}

SCHEDULER_TERMINAL_STATES: Set[SchedulerLifecycleState] = {
    SchedulerLifecycleState.STOPPED,
}


def is_operational(state: SchedulerLifecycleState) -> bool:
    """Scheduler is operational only when RUNNING."""
    return state == SchedulerLifecycleState.RUNNING


def is_terminal(state: SchedulerLifecycleState) -> bool:
    """Check if state is terminal."""
    return state in SCHEDULER_TERMINAL_STATES


def is_valid_scheduler_transition(
    current: SchedulerLifecycleState,
    target: SchedulerLifecycleState,
) -> bool:
    """Check if transition is legal.

    Same-state is always legal (no-op).
    """
    if current == target:
        return True
    allowed = SCHEDULER_LEGAL_TRANSITIONS.get(current, set())
    return target in allowed


class SchedulerLifecycle:
    """Mutable lifecycle tracker for the Execution Scheduler."""

    def __init__(self):
        self._state = SchedulerLifecycleState.UNINITIALIZED

    @property
    def state(self) -> SchedulerLifecycleState:
        return self._state

    def transition(self, target: SchedulerLifecycleState) -> None:
        """Transition to a new state.

        Raises:
            ValueError: if the transition is illegal.
        """
        if not is_valid_scheduler_transition(self._state, target):
            raise ValueError(
                f"Invalid scheduler transition: "
                f"{self._state.value} -> {target.value}"
            )
        self._state = target

    def is_operational(self) -> bool:
        return is_operational(self._state)

    def is_terminal(self) -> bool:
        return is_terminal(self._state)

    def __repr__(self) -> str:
        return f"SchedulerLifecycle(state={self._state.value})"
