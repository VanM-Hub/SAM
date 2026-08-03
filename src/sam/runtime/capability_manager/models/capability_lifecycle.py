"""Capability Lifecycle state enum.

6 states: DECLARED → REGISTERED → CERTIFIED → AVAILABLE → DEPRECATED → RETIRED

Deprecated capabilities remain discoverable.
Retired capabilities are removed from active discovery.

Authority: CAPABILITY_SPEC | R5-001 §2.2
"""

from enum import Enum, auto


class CapabilityLifecycle(Enum):
    """Lifecycle states of a Capability.

    Transition order:
        DECLARED    — capability definition created, not yet registered.
        REGISTERED  — formally registered in the Registry.
        CERTIFIED   — independently certified (descriptor, contract, governance).
        AVAILABLE   — fully available for discovery and use.
        DEPRECATED  — still discoverable but replacement recommended.
        RETIRED     — removed from active discovery; traceable in Audit only.

    Authority: CAPABILITY_SPEC
    """

    DECLARED = auto()
    """Capability definition created, not yet registered."""

    REGISTERED = auto()
    """Formally registered in the Registry."""

    CERTIFIED = auto()
    """Independently certified: descriptor, contract, governance compliance."""

    AVAILABLE = auto()
    """Fully available for discovery and use by any Citizen."""

    DEPRECATED = auto()
    """Still discoverable but replacement is recommended."""

    RETIRED = auto()
    """Removed from active discovery. Traceable in Audit only."""

    def is_discoverable(self) -> bool:
        """Check if capabilities in this state are discoverable.

        Returns:
            True for all states except RETIRED.
        """
        return self is not CapabilityLifecycle.RETIRED

    def is_terminal(self) -> bool:
        """Check if this is a terminal state.

        Returns:
            True only for RETIRED.
        """
        return self is CapabilityLifecycle.RETIRED
