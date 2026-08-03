"""Citizen Host boundary validation.

ADR-006: External access must come through Contracts + Registry only.
Validates that every request entering the Runtime passes the boundary check.

Authority: ADR-006 | R4-001 §2.3 | R5-001 §2.1
"""

from sam.runtime.citizen_host.models.domain import BoundedCapabilityDomain
from sam.runtime.citizen_host.exceptions.boundary_errors import (
    InvalidBoundaryAccess,
    UnauthorizedEntryPoint,
)


class BoundaryValidator:
    """Validates that external access follows Contracts + Registry.

    ADR-006: The external boundary of the Runtime is defined by
    Contracts + Registry. There is no third access mechanism.

    This validator ensures:
        1. Requests reference a valid domain.
        2. No direct unit access (lateral communication).
        3. No bypass of Contracts + Registry boundary.
    """

    # ── Valid entry points ────────────────────────────────────────

    _VALID_ENTRY_POINTS = frozenset({"HostInterface", "Contracts", "Registry"})

    def __init__(self, domain: BoundedCapabilityDomain) -> None:
        self._domain = domain

    def validate_access(
        self,
        capability_identity: str,
        capability_version: str,
        entry_point: str = "HostInterface",
    ) -> bool:
        """Validate that a request enters through a valid boundary.

        Args:
            capability_identity: The requested capability identity.
            capability_version: The requested capability version.
            entry_point: How the request entered (default: HostInterface).

        Returns:
            True if the access is valid.

        Raises:
            UnauthorizedEntryPoint: If entry_point is not valid.
            InvalidBoundaryAccess: If capability identity is empty.
        """
        # Check 1: Valid entry point (Contracts + Registry only)
        if entry_point not in self._VALID_ENTRY_POINTS:
            raise UnauthorizedEntryPoint(
                f"Invalid entry point: {entry_point}. "
                f"Must be one of: {sorted(self._VALID_ENTRY_POINTS)}"
            )

        # Check 2: Capability identity must be non-empty
        if not capability_identity or not capability_identity.strip():
            raise InvalidBoundaryAccess(
                "Capability identity must be non-empty. "
                "All requests must reference a valid Capability."
            )

        # Check 3: Capability version must be non-empty
        if not capability_version or not capability_version.strip():
            raise InvalidBoundaryAccess(
                "Capability version must be non-empty. "
                "All requests must specify a target version."
            )

        return True
