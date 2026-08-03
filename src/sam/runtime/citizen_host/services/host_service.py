"""Citizen Host service orchestrator.

Coordinates all Citizen Host services: health, certification,
boundary validation, and lifecycle management.

Does NOT execute, approve, or audit.

Authority: R4-001 §3.1 | R5-001 §2.1 | I0-001 §2.1
"""

from typing import Optional

from sam.runtime.citizen_host.models.domain import BoundedCapabilityDomain
from sam.runtime.citizen_host.models.health import HealthStatus
from sam.runtime.citizen_host.models.certification import (
    CertificationRequest,
    CertificationStatus,
)
from sam.runtime.citizen_host.interfaces.host_interface import (
    DelegationResult,
    HostInterface,
)
from sam.runtime.citizen_host.services.health_service import HealthService
from sam.runtime.citizen_host.services.certification_service import (
    CertificationService,
)
from sam.runtime.citizen_host.lifecycle.host_lifecycle import (
    HostLifecycle,
    HostLifecycleState,
)
from sam.runtime.citizen_host.validation.boundary_validator import (
    BoundaryValidator,
)
from sam.runtime.citizen_host.exceptions.boundary_errors import (
    InvalidBoundaryAccess,
)


class HostService(HostInterface):
    """Concrete implementation of HostInterface.

    Coordinates:
        - Boundary validation (ADR-006)
        - Health reporting
        - Certification processing
        - Lifecycle management
        - Delegation to Capability Manager

    Must not:
        - Execute operations
        - Approve requests
        - Record audit events
        - Manage Provider/Connector lifecycle
    """

    def __init__(
        self,
        domain: BoundedCapabilityDomain,
        health_service: Optional[HealthService] = None,
        certification_service: Optional[CertificationService] = None,
        lifecycle: Optional[HostLifecycle] = None,
        boundary_validator: Optional[BoundaryValidator] = None,
    ) -> None:
        self._domain = domain
        self._health_service = health_service or HealthService()
        self._certification_service = (
            certification_service or CertificationService()
        )
        self._lifecycle = lifecycle or HostLifecycle()
        self._boundary_validator = (
            boundary_validator or BoundaryValidator(self._domain)
        )

        # Start lifecycle
        self._lifecycle.transition_to(HostLifecycleState.INITIALIZING)
        self._lifecycle.transition_to(HostLifecycleState.RUNNING)

    # ── HostInterface implementation ─────────────────────────────

    def accept_request(
        self,
        capability_identity: str,
        capability_version: str,
    ) -> DelegationResult:
        """Accept a capability request from an external Citizen.

        Validates boundary access first (ADR-006), then delegates
        to Capability Manager.

        Delegation is NOT execution. The Citizen Host only delegates.
        """
        self._ensure_operational()

        # ADR-006: All external access must come through Contracts + Registry
        self._boundary_validator.validate_access(
            capability_identity=capability_identity,
            capability_version=capability_version,
        )

        # Delegate to Capability Manager (not execute!)
        return DelegationResult(
            delegated_to="CapabilityManager",
            accepted=True,
            detail=(
                f"Request for {capability_identity}@"
                f"{capability_version} delegated to Capability Manager"
            ),
        )

    def get_health(self) -> HealthStatus:
        """Report current health status.

        Health is derived from lifecycle state. Always available.
        """
        return self._health_service.compute_health(self._lifecycle.state)

    def request_certification(
        self,
        request: CertificationRequest,
    ) -> CertificationStatus:
        """Process a certification request.

        Certification is deterministic for the same input.
        """
        self._ensure_operational()
        return self._certification_service.evaluate(request)

    def get_domain(self) -> BoundedCapabilityDomain:
        """Return the bounded capability domain.

        The domain is immutable — always returns the same instance.
        """
        return self._domain

    # ── Private helpers ──────────────────────────────────────────

    def _ensure_operational(self) -> None:
        """Ensure the host is in an operational state.

        Raises:
            InvalidBoundaryAccess: If the host is not operational.
        """
        if not self._lifecycle.is_operational():
            raise InvalidBoundaryAccess(
                f"Citizen Host is not operational. "
                f"Current state: {self._lifecycle.state.name}"
            )
