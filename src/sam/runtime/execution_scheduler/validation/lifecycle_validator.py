"""Lifecycle Validator — validates legal state transitions.

Authority: EXECUTION_SPEC §Execution Lifecycle L135-L148
"""

from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionLifecycleState,
    is_valid_transition,
    is_terminal_state,
)
from src.sam.runtime.execution_scheduler.state.execution_state import (
    ExecutionStateRecord,
)


class LifecycleValidator:
    """Validates execution lifecycle transitions."""

    @staticmethod
    def validate_transition(
        record: ExecutionStateRecord,
        target: ExecutionLifecycleState,
    ) -> bool:
        """Validate a transition is legal.

        Args:
            record: The execution record.
            target: Target lifecycle state.

        Returns:
            True if transition is legal.

        Raises:
            ValueError: if transition is illegal.
        """
        if not is_valid_transition(record.lifecycle_state, target):
            raise ValueError(
                f"Invalid transition: "
                f"{record.lifecycle_state.value} -> {target.value}"
            )
        return True

    @staticmethod
    def is_terminal(record: ExecutionStateRecord) -> bool:
        """Check if the execution is in a terminal state."""
        return is_terminal_state(record.lifecycle_state)

    @staticmethod
    def can_transition_from_terminal(
        record: ExecutionStateRecord,
    ) -> bool:
        """ARCHIVED is terminal — no further transitions allowed.

        Returns:
            Always False (no transition from terminal).
        """
        return not is_terminal_state(record.lifecycle_state)
