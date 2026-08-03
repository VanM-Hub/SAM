"""Capability lifecycle transition service.

Manages lifecycle state transitions for published capabilities.

Authority: CAPABILITY_SPEC | R5-001 §2.2
"""

from sam.runtime.capability_manager.models.capability_descriptor import (
    CapabilityDescriptor,
)
from sam.runtime.capability_manager.models.capability_lifecycle import (
    CapabilityLifecycle,
)
from sam.runtime.capability_manager.interfaces.manager_interface import (
    TransitionResult,
)
from sam.runtime.capability_manager.state.capability_state import (
    CapabilityState,
)
from sam.runtime.capability_manager.validation.lifecycle_validator import (
    LifecycleValidator,
)
from sam.runtime.capability_manager.exceptions.capability_errors import (
    CapabilityNotFound,
    DescriptorImmutable,
)


class LifecycleService:
    """Orchestrates Capability lifecycle transitions.

    Flow:
        1. Look up capability by identity.
        2. Validate transition path (LifecycleValidator).
        3. Ensure descriptor is not being modified (immutability check).
        4. Apply transition via CapabilityState.
        5. Return TransitionResult.
    """

    def __init__(self) -> None:
        self._lifecycle_validator = LifecycleValidator()
        # Mapping: identity → current lifecycle state
        self._lifecycles: dict = {}

    def register(self, identity: str, state: CapabilityLifecycle) -> None:
        """Register a capability's initial lifecycle state.

        Args:
            identity: Capability identity.
            state: Initial lifecycle state (usually DECLARED).
        """
        self._lifecycles[identity] = state

    def get_state(self, identity: str) -> CapabilityLifecycle:
        """Get the current lifecycle state of a capability.

        Args:
            identity: Capability identity.

        Returns:
            Current CapabilityLifecycle state.

        Raises:
            CapabilityNotFound: If not found.
        """
        if identity not in self._lifecycles:
            raise CapabilityNotFound(identity)
        return self._lifecycles[identity]

    def transition(
        self,
        identity: str,
        target_state: CapabilityLifecycle,
    ) -> TransitionResult:
        """Transition a capability to a new lifecycle state.

        Args:
            identity: The capability identity.
            target_state: Desired target lifecycle state.

        Returns:
            TransitionResult with from/to states.

        Raises:
            CapabilityNotFound: If capability not found.
            InvalidTransition: If transition path is illegal.
        """
        current = self.get_state(identity)

        # Reject if trying to transition a RETIRED capability
        if CapabilityState.is_terminal(current):
            from sam.runtime.capability_manager.exceptions.capability_errors import (
                InvalidTransition,
            )
            raise InvalidTransition(
                current=current.name,
                target=target_state.name,
                message=(
                    f"Capability '{identity}' is RETIRED — "
                    f"no further transitions allowed."
                ),
            )

        # Validate transition
        self._lifecycle_validator.validate_transition(current, target_state)

        # Apply
        new_state = CapabilityState.transition(current, target_state)
        self._lifecycles[identity] = new_state

        return TransitionResult(
            identity=identity,
            from_state=current,
            to_state=new_state,
            success=True,
            detail=(
                f"Capability '{identity}' transitioned: "
                f"{current.name} → {new_state.name}"
            ),
        )
