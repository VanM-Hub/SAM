"""Runtime-level lifecycle for the Reference Runtime composition (E1-001).

Tracks the composed runtime container through deterministic states:

    CREATED -> COMPOSED -> STARTING -> RUNNING -> STOPPING -> STOPPED
                                                  |
                                                  v
                                                FAILED

Startup is deterministic (fixed transition order); shutdown runs in reverse
order. Any unexpected call path raises LifecycleCompositionError.

Authority: E1-001 Reference Runtime Composition | I0-001 M32
"""

from enum import Enum
from typing import Optional

from .exceptions import LifecycleCompositionError


class RuntimeState(str, Enum):
    """Deterministic runtime lifecycle states (E1-001)."""

    CREATED = "CREATED"
    COMPOSED = "COMPOSED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


#: Valid forward transitions (deterministic).
_TRANSITIONS = {
    RuntimeState.CREATED: {RuntimeState.COMPOSED},
    RuntimeState.COMPOSED: {RuntimeState.STARTING},
    RuntimeState.STARTING: {RuntimeState.RUNNING, RuntimeState.FAILED},
    RuntimeState.RUNNING: {RuntimeState.STOPPING, RuntimeState.FAILED},
    RuntimeState.STOPPING: {RuntimeState.STOPPED, RuntimeState.FAILED},
    RuntimeState.STOPPED: set(),
    RuntimeState.FAILED: set(),
}


class RuntimeLifecycle:
    """State machine for the composed runtime container.

    Attributes:
        state: current RuntimeState.
    """

    def __init__(self, state: RuntimeState = RuntimeState.CREATED) -> None:
        self._state = state

    @property
    def state(self) -> RuntimeState:
        """Current runtime state."""
        return self._state

    def transition_to(self, target: RuntimeState) -> None:
        """Transition to a target state if valid.

        Raises:
            LifecycleCompositionError: if the transition is not permitted.
        """
        if target not in _TRANSITIONS[self._state]:
            raise LifecycleCompositionError(
                "Invalid runtime transition: %s -> %s"
                % (self._state.value, target.value)
            )
        self._state = target

    def is_operational(self) -> bool:
        """True when the runtime accepts external traffic."""
        return self._state == RuntimeState.RUNNING

    def is_stopped(self) -> bool:
        """True when the runtime is fully stopped (or failed)."""
        return self._state in (RuntimeState.STOPPED, RuntimeState.FAILED)

    def transition_to_if(self, target: RuntimeState) -> None:
        """Transition to a target only if it is valid; else no-op.

        Used for defensive failure handling (e.g. force FAILED without
        raising during error handling).
        """
        if target in _TRANSITIONS[self._state]:
            self._state = target


#: Canonical startup order (deterministic).
STARTUP_ORDER = (
    RuntimeState.CREATED,
    RuntimeState.COMPOSED,
    RuntimeState.STARTING,
    RuntimeState.RUNNING,
)

#: Canonical shutdown order (reverse of startup).
SHUTDOWN_ORDER = (
    RuntimeState.RUNNING,
    RuntimeState.STOPPING,
    RuntimeState.STOPPED,
)
