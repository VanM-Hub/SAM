"""Capability Manager lifecycle state machine.

Manager's own operational lifecycle:
UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED

Authority: R4-001 | R5-001 §2.2
"""

from enum import Enum, auto
from typing import Set


class ManagerLifecycleState(Enum):
    """Operational lifecycle states of the Capability Manager.

    Authority: R4-001
    """

    UNINITIALIZED = auto()
    INITIALIZING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()


class ManagerLifecycle:
    """Manages the Capability Manager's own operational lifecycle.

    Allowed transitions:
        UNINITIALIZED → INITIALIZING
        INITIALIZING  → RUNNING
        RUNNING       → STOPPING
        STOPPING      → STOPPED

    STOPPED is terminal.
    """

    _ALLOWED_TRANSITIONS: dict = {
        ManagerLifecycleState.UNINITIALIZED: {ManagerLifecycleState.INITIALIZING},
        ManagerLifecycleState.INITIALIZING: {ManagerLifecycleState.RUNNING},
        ManagerLifecycleState.RUNNING: {ManagerLifecycleState.STOPPING},
        ManagerLifecycleState.STOPPING: {ManagerLifecycleState.STOPPED},
        ManagerLifecycleState.STOPPED: set(),
    }

    def __init__(self) -> None:
        self._state: ManagerLifecycleState = ManagerLifecycleState.UNINITIALIZED

    @property
    def state(self) -> ManagerLifecycleState:
        """Current lifecycle state."""
        return self._state

    def transition_to(self, target: ManagerLifecycleState) -> None:
        """Attempt a state transition.

        Raises:
            ValueError: If the transition is not allowed.
        """
        allowed = self._ALLOWED_TRANSITIONS.get(self._state, set())
        if target not in allowed:
            raise ValueError(
                f"Disallowed manager transition: {self._state.name} → "
                f"{target.name}"
            )
        self._state = target

    def is_operational(self) -> bool:
        """Check if the manager can serve requests.

        Returns:
            True if RUNNING.
        """
        return self._state is ManagerLifecycleState.RUNNING

    def is_terminal(self) -> bool:
        """Check if the manager has reached terminal state.

        Returns:
            True if STOPPED.
        """
        return self._state is ManagerLifecycleState.STOPPED
