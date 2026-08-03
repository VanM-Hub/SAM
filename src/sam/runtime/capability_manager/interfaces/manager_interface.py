"""Capability Manager public interface.

Defines the public contract consumed by Citizen Host (from above)
and Discovery Resolver (from below).

Authority: R5-001 §2.2 | I0-001 §2.2
"""

from dataclasses import dataclass, field
from typing import List, Optional, Protocol

from sam.runtime.capability_manager.models.capability_descriptor import (
    CapabilityDescriptor,
)
from sam.runtime.capability_manager.models.capability_lifecycle import (
    CapabilityLifecycle,
)
from sam.runtime.capability_manager.models.declaration import (
    CapabilityDeclaration,
)


@dataclass(frozen=True)
class PublishResult:
    """Result of a capability publication."""

    descriptor: CapabilityDescriptor
    """The published capability descriptor (immutable)."""

    success: bool = True
    """Whether publication succeeded."""

    detail: Optional[str] = None
    """Optional detail message."""


@dataclass(frozen=True)
class TransitionResult:
    """Result of a lifecycle transition."""

    identity: str
    """The capability identity that was transitioned."""

    from_state: CapabilityLifecycle
    """The state before transition."""

    to_state: CapabilityLifecycle
    """The state after transition."""

    success: bool = True
    """Whether the transition succeeded."""

    detail: Optional[str] = None
    """Optional detail message."""


class CapabilityManagerInterface(Protocol):
    """Public contract of the Capability Manager.

    Consumed by:
        - Citizen Host (publish delegation)
        - Discovery Resolver (capability lookup)

    Operations:
        - publish: validate → create descriptor → store
        - transition: validate → change lifecycle state
        - get_capability: lookup by identity
        - list_capabilities: list with optional filter
        - is_discoverable: check discoverability
        - get_health: report manager health

    Authority: R5-001 §2.2 | I0-001 §2.2
    """

    def publish(self, declaration: CapabilityDeclaration) -> PublishResult:
        """Validate and publish a new Capability.

        Steps:
            1. Validate declaration completeness.
            2. Create immutable CapabilityDescriptor.
            3. Store in managed capability registry.
            4. Return PublishResult with descriptor.

        Args:
            declaration: CapabilityDeclaration to publish.

        Returns:
            PublishResult with the published descriptor.

        Raises:
            InvalidDeclaration: If declaration fails validation.
        """
        ...

    def transition(
        self,
        identity: str,
        target_state: CapabilityLifecycle,
    ) -> TransitionResult:
        """Transition a capability to a new lifecycle state.

        Validates the transition path before applying.

        Args:
            identity: The capability identity.
            target_state: Desired target lifecycle state.

        Returns:
            TransitionResult with from/to states.

        Raises:
            CapabilityNotFound: If capability not found.
            InvalidTransition: If transition path is illegal.
        """
        ...

    def get_capability(
        self,
        identity: str,
    ) -> Optional[CapabilityDescriptor]:
        """Retrieve a capability descriptor by identity.

        Args:
            identity: The capability identity to look up.

        Returns:
            CapabilityDescriptor if found, None otherwise.
        """
        ...

    def list_capabilities(
        self,
        lifecycle_state: Optional[CapabilityLifecycle] = None,
    ) -> List[CapabilityDescriptor]:
        """List capability descriptors, optionally filtered by state.

        Args:
            lifecycle_state: Optional filter by lifecycle state.

        Returns:
            List of matching CapabilityDescriptors.
        """
        ...

    def is_discoverable(self, identity: str) -> bool:
        """Check if a capability is currently discoverable.

        Retired capabilities are NOT discoverable.

        Args:
            identity: The capability identity.

        Returns:
            True if the capability exists and is not RETIRED.
        """
        ...

    def get_health(self) -> str:
        """Report the health status of the Capability Manager.

        Returns:
            'available', 'degraded', or 'unavailable'.
        """
        ...
