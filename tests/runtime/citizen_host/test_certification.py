"""Tests for Citizen Host certification service.

Verifies certification request processing, determinism.

Authority: I2-001 §6.2
"""

from sam.runtime.citizen_host.models.certification import (
    CertificationRequest,
    CertificationStatus,
)
from sam.runtime.citizen_host.services.certification_service import (
    CertificationService,
)


class TestCertificationService:
    """Tests for CertificationService."""

    def setup_method(self) -> None:
        """Set up a fresh CertificationService for each test."""
        self.service = CertificationService()

    def test_valid_request_returns_certified(self) -> None:
        """A valid request returns CERTIFIED status."""
        request = CertificationRequest(
            capability_identity="text_generation",
            capability_version="1.0.0",
        )
        result = self.service.evaluate(request)
        assert result == CertificationStatus.CERTIFIED

    def test_empty_identity_returns_not_certified(self) -> None:
        """Empty capability identity returns NOT_CERTIFIED."""
        request = CertificationRequest(
            capability_identity="",
            capability_version="1.0.0",
        )
        result = self.service.evaluate(request)
        assert result == CertificationStatus.NOT_CERTIFIED

    def test_empty_version_returns_not_certified(self) -> None:
        """Empty capability version returns NOT_CERTIFIED."""
        request = CertificationRequest(
            capability_identity="text_generation",
            capability_version="",
        )
        result = self.service.evaluate(request)
        assert result == CertificationStatus.NOT_CERTIFIED

    def test_whitespace_identity_returns_not_certified(self) -> None:
        """Whitespace-only identity returns NOT_CERTIFIED."""
        request = CertificationRequest(
            capability_identity="   ",
            capability_version="1.0.0",
        )
        result = self.service.evaluate(request)
        assert result == CertificationStatus.NOT_CERTIFIED

    def test_determinism_same_input_same_output(self) -> None:
        """Determinism: same request always returns same result."""
        request = CertificationRequest(
            capability_identity="text_generation",
            capability_version="1.0.0",
        )
        results = [self.service.evaluate(request) for _ in range(5)]
        assert all(r == CertificationStatus.CERTIFIED for r in results)

    def test_request_with_requested_by(self) -> None:
        """Certification request can include requester identity."""
        request = CertificationRequest(
            capability_identity="text_generation",
            capability_version="1.0.0",
            requested_by="citizen-001",
        )
        result = self.service.evaluate(request)
        assert result == CertificationStatus.CERTIFIED
        assert request.requested_by == "citizen-001"
