"""
citizen_host — Citizen Host Unit (Reference Runtime Unit 1)

Surface unit of the Reference Runtime. Entry point for all external interactions.
Owns one bounded capability domain. Exposes health. Supports certification.

Authority: CITIZEN_SPEC | GOVERNANCE | ADR-000 | ADR-006
Derived from: R4-001 §3.1 | R4-002 §2.2 | R5-001 §2.1 | I0-001 §2.1 | I1-001 §2.1
"""

from sam.runtime.citizen_host.models.domain import BoundedCapabilityDomain
from sam.runtime.citizen_host.models.health import HealthStatus
from sam.runtime.citizen_host.models.certification import CertificationRequest, CertificationStatus
from sam.runtime.citizen_host.interfaces.host_interface import HostInterface
from sam.runtime.citizen_host.exceptions.boundary_errors import (
    InvalidBoundaryAccess,
    UnauthorizedEntryPoint,
    DirectUnitAccess,
)

__all__ = [
    # Models
    "BoundedCapabilityDomain",
    "HealthStatus",
    "CertificationRequest",
    "CertificationStatus",
    # Interface
    "HostInterface",
    # Exceptions
    "InvalidBoundaryAccess",
    "UnauthorizedEntryPoint",
    "DirectUnitAccess",
]
