"""Discovery Resolver — Unit 3 Reference Runtime.

Implements ADR-002 capability resolution:
    exact-preferred → compatible fallback → tie-break identity+version

Public API:
    DiscoveryResolver    — main resolver (implements DiscoveryResolverInterface)
    CapabilityRequest    — request model
    ResolutionResult     — result model
    RegistryEntry        — registry entry model
    ResolutionStatus     — result status enum
    ResolverLifecycleState — lifecycle state enum
    ResolverLifecycle    — lifecycle state machine

Authority: R4-001 §3.3 | R4-002 §2.4 | R5-001 §2.3 | I0-001 §2.3
"""

from sam.runtime.discovery_resolver.services.resolver_service import (
    DiscoveryResolver,
)
from sam.runtime.discovery_resolver.models.capability_request import (
    CapabilityRequest,
)
from sam.runtime.discovery_resolver.models.resolution_result import (
    ResolutionResult,
    ResolutionStatus,
)
from sam.runtime.discovery_resolver.models.registry_entry import (
    RegistryEntry,
)
from sam.runtime.discovery_resolver.lifecycle.resolver_lifecycle import (
    ResolverLifecycle,
    ResolverLifecycleState,
)

__all__ = [
    "DiscoveryResolver",
    "CapabilityRequest",
    "ResolutionResult",
    "ResolutionStatus",
    "RegistryEntry",
    "ResolverLifecycle",
    "ResolverLifecycleState",
]
