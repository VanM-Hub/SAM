"""Capability Descriptor — immutable representation of a Capability.

Every Capability publishes an immutable descriptor containing:
identity, version, contract reference, lifecycle state, certification status.

Authority: CAPABILITY_SPEC | R5-001 §2.2 | I0-001 §2.2
"""

from dataclasses import dataclass, field
from typing import List, Optional

from sam.runtime.capability_manager.models.capability_lifecycle import (
    CapabilityLifecycle,
)


@dataclass(frozen=True)
class CapabilityDescriptor:
    """The immutable declaration of a Capability.

    Capabilities describe behavior — never implementation.
    Once published, the descriptor cannot be modified.

    Invariants:
        - identity must be non-empty and unique.
        - identity must not contain implementation names.
        - version: Major.Minor.Patch (string).
        - lifecycle state progresses forward only.
        - descriptor is frozen after publication.

    Authority: CAPABILITY_SPEC | R5-001 §2.2
    """

    identity: str
    """Globally unique capability identifier, e.g. 'memory.lookup'."""

    name: str
    """Human-readable capability name."""

    version: str
    """Semantic version: Major.Minor.Patch, e.g. '1.0.0'."""

    description: str = ""
    """Description of the capability's purpose."""

    owner_citizen: str = ""
    """The Citizen that owns this capability."""

    inputs: List[str] = field(default_factory=list)
    """Expected input identifiers."""

    outputs: List[str] = field(default_factory=list)
    """Expected output identifiers."""

    constraints: List[str] = field(default_factory=list)
    """Operational constraints on this capability."""

    compatibility: List[str] = field(default_factory=list)
    """Compatible capability identities or version ranges."""

    lifecycle_state: CapabilityLifecycle = CapabilityLifecycle.DECLARED
    """Current lifecycle state of the capability."""

    certification_status: Optional[str] = None
    """Certification status: 'certified', 'not-certified', or None if not evaluated."""

    metadata: Optional[dict] = field(default_factory=dict)
    """Optional extension metadata."""

    def validate_identity(self) -> bool:
        """Validate that identity is non-empty and valid.

        Returns:
            True if identity is non-empty.
        """
        return bool(self.identity and self.identity.strip())

    def is_discoverable(self) -> bool:
        """Check if this capability is currently discoverable.

        Retired capabilities are NOT discoverable for new requests.
        Deprecated capabilities remain discoverable.

        Returns:
            True if lifecycle state is not RETIRED.
        """
        return self.lifecycle_state != CapabilityLifecycle.RETIRED

    def is_immutable(self) -> bool:
        """Check if the descriptor is in an immutable state.

        Once past DECLARED, the descriptor is immutable.

        Returns:
            True if lifecycle_state is not DECLARED.
        """
        return self.lifecycle_state != CapabilityLifecycle.DECLARED

    def __repr__(self) -> str:
        return (
            f"CapabilityDescriptor("
            f"identity={self.identity!r}@"
            f"{self.version}, "
            f"state={self.lifecycle_state.name})"
        )
