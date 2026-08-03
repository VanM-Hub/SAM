"""Session lifecycle manager — manages compliance session state transitions."""

from __future__ import annotations

from typing import Set

from ..models.session_state import SessionState
from ..exceptions.compliance_errors import InvalidSessionStateError, SessionImmutableError


class SessionLifecycle:
    """Manages compliance session state transitions.

    Per P1-001 §7.1 lifecycle:
    INITIATED → EVIDENCE_COLLECTION → ANALYSIS → PRELIMINARY_VERDICT → REVIEW → FINAL_VERDICT → ARCHIVED
    """

    # Valid transitions (strict ordering)
    _TRANSITIONS = {
        SessionState.INITIATED: {SessionState.EVIDENCE_COLLECTION},
        SessionState.EVIDENCE_COLLECTION: {SessionState.ANALYSIS},
        SessionState.ANALYSIS: {SessionState.PRELIMINARY_VERDICT},
        SessionState.PRELIMINARY_VERDICT: {SessionState.REVIEW, SessionState.FINAL_VERDICT},
        SessionState.REVIEW: {SessionState.FINAL_VERDICT},
        SessionState.FINAL_VERDICT: {SessionState.ARCHIVED},
        SessionState.ARCHIVED: set(),  # terminal
    }

    def __init__(self) -> None:
        self._state = SessionState.INITIATED

    @property
    def state(self) -> SessionState:
        """Current lifecycle state."""
        return self._state

    def transition_to(self, target: SessionState) -> None:
        """Transition to a new state.

        Raises InvalidSessionStateError if transition is not allowed.
        Raises SessionImmutableError if current state is terminal.
        """
        if self._state in SessionState.terminal_states():
            raise SessionImmutableError("session")

        allowed = self._TRANSITIONS.get(self._state, set())
        if target not in allowed:
            raise InvalidSessionStateError(
                self._state.value,
                ", ".join(s.value for s in allowed),
            )

        self._state = target

    def can_transition_to(self, target: SessionState) -> bool:
        """Check if a transition to the target state is valid."""
        allowed = self._TRANSITIONS.get(self._state, set())
        return target in allowed

    def is_terminal(self) -> bool:
        """Return True if the lifecycle is in a terminal state."""
        return self._state in SessionState.terminal_states()

    def is_active(self) -> bool:
        """Return True if the lifecycle is in an active state."""
        return self._state in SessionState.active_states()

    @classmethod
    def valid_transitions(cls, state: SessionState) -> Set[SessionState]:
        """Return the set of valid next states from a given state."""
        return cls._TRANSITIONS.get(state, set())

    def reset(self) -> None:
        """Reset the lifecycle to INITIATED."""
        self._state = SessionState.INITIATED

    def get_state(self) -> SessionState:
        """Get current state."""
        return self._state
