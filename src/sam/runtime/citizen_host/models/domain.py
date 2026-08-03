"""Citizen Host domain models — BoundedCapabilityDomain.

R1: Own bounded capability domain.
One Runtime = one domain = one Citizen identity.

Authority: CITIZEN_SPEC | GOVERNANCE Runtime Governance
Source: R4-001 §3.1 | R5-001 §2.1 | I0-001 §2.1
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class BoundedCapabilityDomain:
    """The identity of this Runtime as a Citizen.

    A BoundedCapabilityDomain is the governance boundary of this Runtime.
    It defines which Capabilities this Runtime owns and governs.

    Invariants:
        - One Runtime has exactly one BoundedCapabilityDomain.
        - The domain cannot be changed after creation (frozen).
        - The domain does not confer architectural privilege.

    Authority: CITIZEN_SPEC | GOVERNANCE
    """

    identity: str
    """Unique identity of this domain — the Citizen's name/key."""

    display_name: str
    """Human-readable display name."""

    description: Optional[str] = None
    """Optional description of the domain's purpose."""

    version: str = "1.0.0"
    """Domain version — follows semantic versioning."""

    def validate(self) -> bool:
        """Validate domain integrity.

        Returns:
            True if the domain identity is non-empty and valid.
        """
        return bool(self.identity and self.identity.strip())

    def __repr__(self) -> str:
        return (
            f"BoundedCapabilityDomain("
            f"identity={self.identity!r}, "
            f"version={self.version!r})"
        )
