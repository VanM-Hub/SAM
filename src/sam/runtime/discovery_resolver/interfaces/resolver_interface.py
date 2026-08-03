"""Discovery Resolver public interface.

Defines the public contract consumed by consumers
of capability discovery and resolution.

Authority: R5-001 §2.3 | I0-001 §2.3
"""

from typing import Protocol

from sam.runtime.discovery_resolver.models.capability_request import (
    CapabilityRequest,
)
from sam.runtime.discovery_resolver.models.resolution_result import (
    ResolutionResult,
)
from sam.runtime.discovery_resolver.models.registry_entry import (
    RegistryEntry,
)


class DiscoveryResolverInterface(Protocol):
    """Public contract of the Discovery Resolver.

    Operations:
        resolve: Resolve a CapabilityRequest → ResolutionResult.
        register_entry: Register a capability entry for resolution.
        get_health: Report resolver health status.

    Authority: R5-001 §2.3 | I0-001 §2.3
    """

    def resolve(self, request: CapabilityRequest) -> ResolutionResult:
        """Resolve a Capability Request to a single capability.

        Implements ADR-002:
            1. Exact match preferred (identity + version).
            2. Compatible fallback (same identity, same major).
            3. Deterministic tie-break (identity + version sort).

        Args:
            request: The capability request to resolve.

        Returns:
            ResolutionResult with status and resolved capability.
        """
        ...

    def register_entry(self, entry: RegistryEntry) -> None:
        """Register a capability entry in the resolver's registry.

        Entries should come from Capability Manager publication
        or direct registration for testing.

        Args:
            entry: The RegistryEntry to register.

        Raises:
            InvalidRegistryEntry: If the entry is invalid.
        """
        ...

    def get_health(self) -> str:
        """Report the health status of the Discovery Resolver.

        Returns:
            'available', 'degraded', or 'unavailable'.
        """
        ...
