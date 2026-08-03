"""ContractEnforcerLifecycle — 5-state lifecycle machine.

Authority: I2-004 §4.6
"""

from enum import Enum
from typing import Dict, FrozenSet, Set


class ContractEnforcerLifecycleState(str, Enum):
    """Lifecycle states for Contract Enforcer Unit.

    Path: UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED
    """
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"

    def is_operational(self) -> bool:
        """Only RUNNING is operational."""
        return self == ContractEnforcerLifecycleState.RUNNING

    def is_terminal(self) -> bool:
        """STOPPED is terminal."""
        return self == ContractEnforcerLifecycleState.STOPPED


# Allowed transitions: from → set of allowed to-states
_ALLOWED_TRANSITIONS: Dict[ContractEnforcerLifecycleState, FrozenSet[ContractEnforcerLifecycleState]] = {
    ContractEnforcerLifecycleState.UNINITIALIZED: frozenset({
        ContractEnforcerLifecycleState.INITIALIZING,
    }),
    ContractEnforcerLifecycleState.INITIALIZING: frozenset({
        ContractEnforcerLifecycleState.RUNNING,
    }),
    ContractEnforcerLifecycleState.RUNNING: frozenset({
        ContractEnforcerLifecycleState.STOPPING,
    }),
    ContractEnforcerLifecycleState.STOPPING: frozenset({
        ContractEnforcerLifecycleState.STOPPED,
    }),
    ContractEnforcerLifecycleState.STOPPED: frozenset(),  # terminal
}


class ContractEnforcerLifecycle:
    """State machine governing Contract Enforcer lifecycle."""

    def __init__(self) -> None:
        self._state = ContractEnforcerLifecycleState.UNINITIALIZED

    @property
    def state(self) -> ContractEnforcerLifecycleState:
        return self._state

    def transition_to(self, target: ContractEnforcerLifecycleState) -> None:
        """Attempt transition to target state.

        Args:
            target: Desired lifecycle state.

        Raises:
            ValueError: if transition is not allowed.
        """
        if target == self._state:
            return  # no-op

        allowed = _ALLOWED_TRANSITIONS.get(self._state, frozenset())
        if target not in allowed:
            raise ValueError(
                f"Invalid transition: {self._state.value} → {target.value}"
            )
        self._state = target

    def is_operational(self) -> bool:
        return self._state.is_operational()

    def is_terminal(self) -> bool:
        return self._state.is_terminal()
