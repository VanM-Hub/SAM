"""ContractState — state machine for individual contract operations.

Tracks the state of contract registration and negotiation requests.
"""

from enum import Enum
from typing import Dict, FrozenSet


class ContractOperationState(str, Enum):
    """States for a contract operation."""
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    NEGOTIATING = "NEGOTIATING"
    NEGOTIATED = "NEGOTIATED"
    INVALID = "INVALID"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS: Dict[ContractOperationState, FrozenSet[ContractOperationState]] = {
    ContractOperationState.CREATED: frozenset({
        ContractOperationState.VALIDATING,
    }),
    ContractOperationState.VALIDATING: frozenset({
        ContractOperationState.VALID,
        ContractOperationState.INVALID,
    }),
    ContractOperationState.VALID: frozenset({
        ContractOperationState.NEGOTIATING,
    }),
    ContractOperationState.NEGOTIATING: frozenset({
        ContractOperationState.NEGOTIATED,
        ContractOperationState.FAILED,
    }),
    ContractOperationState.INVALID: frozenset(),  # terminal
    ContractOperationState.NEGOTIATED: frozenset(),  # terminal
    ContractOperationState.FAILED: frozenset(),  # terminal
}


class ContractState:
    """State machine for contract operations."""

    def __init__(self) -> None:
        self._state = ContractOperationState.CREATED

    @property
    def state(self) -> ContractOperationState:
        return self._state

    def transition_to(self, target: ContractOperationState) -> None:
        """Attempt transition.

        Raises ValueError if transition not allowed.
        """
        if target == self._state:
            return
        allowed = _ALLOWED_TRANSITIONS.get(self._state, frozenset())
        if target not in allowed:
            raise ValueError(
                f"Invalid contract state transition: "
                f"{self._state.value} → {target.value}"
            )
        self._state = target

    def is_terminal(self) -> bool:
        return self._state in (
            ContractOperationState.INVALID,
            ContractOperationState.NEGOTIATED,
            ContractOperationState.FAILED,
        )

    def is_valid(self) -> bool:
        return self._state in (
            ContractOperationState.VALID,
            ContractOperationState.NEGOTIATING,
            ContractOperationState.NEGOTIATED,
        )
