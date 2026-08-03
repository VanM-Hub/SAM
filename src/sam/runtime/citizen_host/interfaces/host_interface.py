"""Citizen Host public interface — HostInterface.

The single surface entry point for all external interactions.
Delegates capability declarations to Capability Manager.

Authority: R4-001 §3.1 | R5-001 §2.1 | I0-001 §2.1
"""

from dataclasses import dataclass, field
from typing import Optional, Protocol

from sam.runtime.citizen_host.models.domain import BoundedCapabilityDomain
from sam.runtime.citizen_host.models.health import HealthStatus
from sam.runtime.citizen_host.models.certification import (
    CertificationRequest,
    CertificationStatus,
)


@dataclass(frozen=True)
class DelegationResult:
    """Result of delegating a request down the Runtime chain.

    The Citizen Host does NOT execute, approve, or record.
    It only delegates to Capability Manager and reports the result.

    Authority: R5-001 §2.1
    """

    delegated_to: str
    """The unit that received the delegation (e.g., 'CapabilityManager')."""

    accepted: bool
    """Whether the delegation was accepted."""

    detail: Optional[str] = None
    """Optional detail about the delegation result."""


class HostInterface(Protocol):
    """Public surface of the Citizen Host.

    This is the ONLY entry point for external interactions into the Runtime.
    All requests must pass through this interface.

    Design:
        - accept_request: delegates to Capability Manager.
        - get_health: returns current health status.
        - request_certification: processes certification request.
        - get_domain: returns the bounded capability domain.

    Authority: R4-001 §3.1 | R5-001 §2.1 | I0-001 §2.1
    """

    def accept_request(
        self,
        capability_identity: str,
        capability_version: str,
    ) -> DelegationResult:
        """Accept a capability request from an external Citizen.

        Delegates the request to Capability Manager via the Runtime chain.
        Does NOT execute, approve, or audit.

        Args:
            capability_identity: The identity of the requested Capability.
            capability_version: The version of the requested Capability.

        Returns:
            DelegationResult indicating acceptance or rejection.

        Raises:
            InvalidBoundaryAccess: If the request did not enter through
                Contracts + Registry (ADR-006).
        """
        ...

    def get_health(self) -> HealthStatus:
        """Report the current health status of the Runtime.

        Health status is always available for external query.

        Returns:
            Current HealthStatus: AVAILABLE, DEGRADED, or UNAVAILABLE.
        """
        ...

    def request_certification(
        self,
        request: CertificationRequest,
    ) -> CertificationStatus:
        """Process a certification request for a Capability.

        Certification result is deterministic for the same input.

        Args:
            request: CertificationRequest with capability identity and version.

        Returns:
            CertificationStatus: CERTIFIED, NOT_CERTIFIED, or PENDING.
        """
        ...

    def get_domain(self) -> BoundedCapabilityDomain:
        """Return the bounded capability domain of this Runtime.

        Returns:
            The single BoundedCapabilityDomain this Citizen Host owns.
        """
        ...
