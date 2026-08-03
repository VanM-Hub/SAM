"""Citizen Host certification service.

R8: Support certification.
Processes CertificationRequests and returns deterministic CertificationStatus.

Authority: GOVERNANCE | R4-001 §3.1 | R5-001 §2.1
"""

from sam.runtime.citizen_host.models.certification import (
    CertificationRequest,
    CertificationStatus,
)


class CertificationService:
    """Processes certification requests for Capabilities.

    Certification is deterministic: the same request always yields
    the same result.

    Current implementation: all valid requests pass certification.
    The certification criteria are defined by the Capability's
    compliance with its Specification. This is a baseline
    implementation that can be extended with actual verification
    logic as the Runtime matures.
    """

    def evaluate(self, request: CertificationRequest) -> CertificationStatus:
        """Evaluate a certification request.

        Deterministic result for the same input.

        Args:
            request: CertificationRequest with capability identity and version.

        Returns:
            CERTIFIED if the request is valid and meets criteria.
            NOT_CERTIFIED if the request is invalid.
            PENDING is reserved for async certification flows (future).
        """
        if not request.validate():
            return CertificationStatus.NOT_CERTIFIED

        # Baseline: all structurally valid capabilities pass certification.
        # This will be extended with actual verification logic.
        return CertificationStatus.CERTIFIED
