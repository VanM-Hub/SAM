"""Citizen Host certification models — CertificationRequest, CertificationStatus.

R8: Support certification.
The Runtime must be able to receive and process certification requests.

Authority: GOVERNANCE Runtime Governance
Source: R4-001 §3.1 | R5-001 §2.1 | I0-001 §2.1
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class CertificationStatus(Enum):
    """Result of a certification request.

    States:
        CERTIFIED      — Capability has been certified.
        NOT_CERTIFIED  — Capability does not meet certification criteria.
        PENDING        — Certification is in progress.

    Authority: GOVERNANCE
    """

    CERTIFIED = auto()
    NOT_CERTIFIED = auto()
    PENDING = auto()


@dataclass(frozen=True)
class CertificationRequest:
    """A request to certify a capability.

    Invariants:
        - capability_identity must be non-empty.
        - Certification result is deterministic for same input.

    Authority: GOVERNANCE
    """

    capability_identity: str
    """Identity of the Capability being certified."""

    capability_version: str
    """Version of the Capability being certified."""

    requested_by: Optional[str] = None
    """Optional identity of the requesting Citizen."""

    metadata: Optional[dict] = field(default_factory=dict)
    """Optional metadata for the certification request."""

    def validate(self) -> bool:
        """Validate that the request has required fields.

        Returns:
            True if capability_identity and capability_version are non-empty.
        """
        return bool(
            self.capability_identity
            and self.capability_identity.strip()
            and self.capability_version
            and self.capability_version.strip()
        )

    def __repr__(self) -> str:
        return (
            f"CertificationRequest("
            f"capability={self.capability_identity!r}@"
            f"{self.capability_version!r})"
        )
