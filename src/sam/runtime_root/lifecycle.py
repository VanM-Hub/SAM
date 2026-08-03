"""Runtime lifecycle for the Reference Runtime root (E1-001).

Tracks the composed runtime through deterministic states:

    CREATED -> BUILT -> STARTED -> STOPPED -> DISPOSED

Determinism is enforced by a fixed transition table: any invalid call path
raises RuntimeCompositionError.

Authority: E1-001 COMPOSITION ROOT | I0-001 M32
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from .exceptions import LifecycleCompositionError


class RuntimeState(str, Enum):
    """Deterministic runtime lifecycle states (E1-001)."""

    CREATED = "CREATED"
    BUILT = "BUILT"
    STARTED = "STARTED"
    STOPPED = "STOPPED"
    DISPOSED = "DISPOSED"


#: Valid forward transitions (deterministic).
_TRANSITIONS = {
    RuntimeState.CREATED: {RuntimeState.BUILT},
    RuntimeState.BUILT: {RuntimeState.STARTED, RuntimeState.STOPPED},
    RuntimeState.STARTED: {RuntimeState.STOPPED},
    RuntimeState.STOPPED: {RuntimeState.STARTED, RuntimeState.DISPOSED},
    RuntimeState.DISPOSED: set(),
}


class RuntimeLifecycle:
    """State machine for the composed runtime root.

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

    def transition_to_if(self, target: RuntimeState) -> None:
        """Transition to a target only if valid; else no-op.

        Used for defensive failure handling without raising mid-error.
        """
        if target in _TRANSITIONS[self._state]:
            self._state = target

    def is_running(self) -> bool:
        """True iff the runtime is in the STARTED state."""
        return self._state == RuntimeState.STARTED

    def is_disposed(self) -> bool:
        """True iff the runtime reached the terminal DISPOSED state."""
        return self._state == RuntimeState.DISPOSED


#: Canonical lifecycle order (deterministic).
LIFECYCLE_ORDER = (
    RuntimeState.CREATED,
    RuntimeState.BUILT,
    RuntimeState.STARTED,
    RuntimeState.STOPPED,
    RuntimeState.DISPOSED,
)
