"""Lifecycle Validator — validates approval lifecycle transitions."""

from src.sam.runtime.approval_coordinator.state.approval_state import (
    ApprovalLifecycleState,
    ApprovalState,
)
from src.sam.runtime.approval_coordinator.exceptions.approval_errors import (
    InvalidTransitionError,
)


class LifecycleValidator:
    """Validates approval lifecycle transitions against APPROVAL_SPEC."""

    @staticmethod
    def validate_transition(
        current: ApprovalLifecycleState,
        target: ApprovalLifecycleState,
    ) -> bool:
        """Check whether a transition is legal.

        Returns True if legal.
        Raises InvalidTransitionError if not.
        """
        from src.sam.runtime.approval_coordinator.state.approval_state import (
            _LEGAL_TRANSITIONS,
        )

        if current == target:
            return True  # No-op is always valid

        if current == ApprovalLifecycleState.ARCHIVED:
            raise InvalidTransitionError(
                f"Cannot transition from terminal state ARCHIVED"
            )

        allowed = _LEGAL_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidTransitionError(
                f"Illegal transition: {current.value} → {target.value}"
            )

        return True

    @staticmethod
    def is_valid(
        current: ApprovalLifecycleState,
        target: ApprovalLifecycleState,
    ) -> bool:
        """Non-raising check."""
        try:
            LifecycleValidator.validate_transition(current, target)
            return True
        except InvalidTransitionError:
            return False
