"""Lifecycle transition validation.

Validates that lifecycle transitions follow the allowed path:
DECLARED → REGISTERED → CERTIFIED → AVAILABLE → DEPRECATED → RETIRED

Authority: R5-001 §2.2 | CAPABILITY_SPEC
"""

from sam.runtime.capability_manager.models.capability_lifecycle import (
    CapabilityLifecycle,
)
from sam.runtime.capability_manager.state.capability_state import (
    CapabilityState,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    InvalidTransition,
)


class LifecycleValidator:
    """Validates Capability lifecycle transitions.

    Delegates to CapabilityState for transition path validation.
    Adds business-level checks (retired → no transitions, etc.).
    """

    def validate_transition(
        self,
        from_state: CapabilityLifecycle,
        to_state: CapabilityLifecycle,
    ) -> bool:
        """Validate a lifecycle transition.

        Args:
            from_state: Current lifecycle state.
            to_state: Desired target state.

        Returns:
            True if transition is valid.

        Raises:
            InvalidTransition: If the transition is not allowed.
        """
        # Terminal state — no forward transitions
        if CapabilityState.is_terminal(from_state):
            raise InvalidTransition(
                current=from_state.name,
                target=to_state.name,
                message=(
                    f"Cannot transition from terminal state '{from_state.name}'"
                ),
            )

        # Same state — no-op is valid
        if from_state == to_state:
            return True

        # Check transition path
        if not CapabilityState.can_transition(from_state, to_state):
            raise InvalidTransition(
                current=from_state.name,
                target=to_state.name,
            )

        return True

    def validate_declared_to_registered(
        self,
        state: CapabilityLifecycle,
    ) -> bool:
        """Validate DECLARED → REGISTERED transition prerequisites.

        The capability must be in DECLARED state and the descriptor
        must be complete.

        Args:
            state: Current lifecycle state.

        Returns:
            True if ready for registration.

        Raises:
            InvalidTransition: If not in DECLARED state.
        """
        if state != CapabilityLifecycle.DECLARED:
            raise InvalidTransition(
                current=state.name,
                target=CapabilityLifecycle.REGISTERED.name,
                message="Can only register from DECLARED state",
            )
        return True
