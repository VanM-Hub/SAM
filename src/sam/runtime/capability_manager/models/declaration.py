"""Capability Declaration — request to publish a Capability.

A Declaration is the input to the Capability Manager's publish operation.
It contains all fields needed to create a CapabilityDescriptor.

Authority: CAPABILITY_SPEC | R5-001 §2.2
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class CapabilityDeclaration:
    """A request to publish a new Capability.

    The declaration contains everything needed to construct a
    CapabilityDescriptor. Once validated, it becomes an immutable
    descriptor.

    Invariants:
        - identity must be non-empty.
        - identity must NOT contain implementation names (e.g., 'openai').
        - name must be non-empty.
        - version must follow Major.Minor.Patch format.

    Authority: CAPABILITY_SPEC
    """

    identity: str
    """Globally unique capability identifier, e.g. 'memory.lookup'."""

    name: str
    """Human-readable capability name."""

    version: str
    """Semantic version: Major.Minor.Patch."""

    owner_citizen: str = ""
    """The Citizen that owns this capability."""

    description: str = ""
    """Description of the capability's purpose."""

    inputs: List[str] = field(default_factory=list)
    """Expected input identifiers."""

    outputs: List[str] = field(default_factory=list)
    """Expected output identifiers."""

    constraints: List[str] = field(default_factory=list)
    """Operational constraints."""

    compatibility: List[str] = field(default_factory=list)
    """Compatible versions or identities."""

    metadata: Optional[dict] = field(default_factory=dict)
    """Optional extension metadata."""

    def validate_required(self) -> bool:
        """Validate that required fields are non-empty.

        Returns:
            True if identity, name, and version are non-empty.
        """
        return all(
            [
                bool(self.identity and self.identity.strip()),
                bool(self.name and self.name.strip()),
                bool(self.version and self.version.strip()),
            ]
        )
