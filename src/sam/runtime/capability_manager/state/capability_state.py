"""Capability State Machine.

Defines allowed lifecycle transitions:
DECLARED → REGISTERED → CERTIFIED → AVAILABLE → DEPRECATED → RETIRED

Deprecated may return to Available. Retired is terminal.

Authority: CAPABILITY_SPEC | R5-001 §2.2 | R5-001 C2
"""

from typing import Set

from sam.runtime.capability_manager.models.capability_lifecycle import (
    CapabilityLifecycle,
)


class CapabilityState:
    """Manages Capability lifecycle state transitions.

    Only transitions through allowed paths. Any disallowed transition
    raises ValueError.

    Allowed transitions:
        DECLARED   → REGISTERED
        REGISTERED → CERTIFIED
        CERTIFIED  → AVAILABLE
        AVAILABLE  → DEPRECATED
        DEPRECATED → AVAILABLE (recovery), RETIRED
        RETIRED    → (none — terminal)

    Invariants:
        - State cannot skip intermediate steps.
        - RETIRED is terminal — no further transitions.
        - DEPRECATED is reversible (can return to AVAILABLE).
    """

    _ALLOWED_TRANSITIONS: dict = {
        CapabilityLifecycle.DECLARED: {
            CapabilityLifecycle.REGISTERED,
        },
        CapabilityLifecycle.REGISTERED: {
            CapabilityLifecycle.CERTIFIED,
        },
        CapabilityLifecycle.CERTIFIED: {
            CapabilityLifecycle.AVAILABLE,
        },
        CapabilityLifecycle.AVAILABLE: {
            CapabilityLifecycle.DEPRECATED,
        },
        CapabilityLifecycle.DEPRECATED: {
            CapabilityLifecycle.AVAILABLE,
            CapabilityLifecycle.RETIRED,
        },
        CapabilityLifecycle.RETIRED: set(),  # terminal
    }

    @classmethod
    def can_transition(
        cls,
        from_state: CapabilityLifecycle,
        to_state: CapabilityLifecycle,
    ) -> bool:
        """Check if a transition is allowed.

        Args:
            from_state: Current lifecycle state.
            to_state: Desired target state.

        Returns:
            True if the transition path is allowed.
        """
        allowed = cls._ALLOWED_TRANSITIONS.get(from_state, set())
        return to_state in allowed

    @classmethod
    def transition(
        cls,
        from_state: CapabilityLifecycle,
        to_state: CapabilityLifecycle,
    ) -> CapabilityLifecycle:
        """Execute a state transition.

        Args:
            from_state: Current lifecycle state.
            to_state: Desired target state.

        Returns:
            The new state after transition.

        Raises:
            ValueError: If the transition is not allowed.
        """
        # Same-state is a valid no-op.
        if from_state == to_state:
            return to_state

        if not cls.can_transition(from_state, to_state):
            allowed = cls._ALLOWED_TRANSITIONS.get(from_state, set())
            raise ValueError(
                f"Disallowed transition: {from_state.name} → "
                f"{to_state.name}. Allowed: "
                f"{[s.name for s in sorted(allowed, key=lambda s: s.name)]}"
                if allowed
                else f"Disallowed transition: {from_state.name} → "
                f"{to_state.name}. No transitions from terminal state."
            )
        return to_state

    @classmethod
    def is_terminal(cls, state: CapabilityLifecycle) -> bool:
        """Check if a state is terminal.

        Returns:
            True if RETIRED.
        """
        return state is CapabilityLifecycle.RETIRED

    @classmethod
    def is_reversible(cls, state: CapabilityLifecycle) -> bool:
        """Check if a state transition can be reversed.

        Returns:
            True if DEPRECATED (can return to AVAILABLE).
        """
        return state is CapabilityLifecycle.DEPRECATED
