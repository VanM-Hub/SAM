"""Tests for Citizen Host boundary validation.

Verifies ADR-006 compliance: all external access through Contracts + Registry.
Validates boundary errors and entry point restrictions.

Authority: I2-001 §6.2 | ADR-006
"""

import pytest

from sam.runtime.citizen_host import BoundedCapabilityDomain
from sam.runtime.citizen_host.validation.boundary_validator import (
    BoundaryValidator,
)
from sam.runtime.citizen_host.exceptions.boundary_errors import (
    InvalidBoundaryAccess,
    UnauthorizedEntryPoint,
)


class TestBoundaryValidator:
    """Tests for BoundaryValidator — ADR-006 compliance."""

    def setup_method(self) -> None:
        """Set up domain and validator for each test."""
        self.domain = BoundedCapabilityDomain(
            identity="com.example.runtime",
            display_name="Example Runtime",
        )
        self.validator = BoundaryValidator(self.domain)

    def test_valid_access_through_host_interface(self) -> None:
        """Access through HostInterface is valid."""
        result = self.validator.validate_access(
            capability_identity="text_generation",
            capability_version="1.0.0",
            entry_point="HostInterface",
        )
        assert result is True

    def test_valid_access_through_contracts(self) -> None:
        """Access through Contracts entry point is valid."""
        result = self.validator.validate_access(
            capability_identity="text_generation",
            capability_version="1.0.0",
            entry_point="Contracts",
        )
        assert result is True

    def test_valid_access_through_registry(self) -> None:
        """Access through Registry entry point is valid."""
        result = self.validator.validate_access(
            capability_identity="text_generation",
            capability_version="1.0.0",
            entry_point="Registry",
        )
        assert result is True

    def test_invalid_entry_point_raises_unauthorized(self) -> None:
        """Access through invalid entry point raises UnauthorizedEntryPoint."""
        with pytest.raises(UnauthorizedEntryPoint) as exc_info:
            self.validator.validate_access(
                capability_identity="text_generation",
                capability_version="1.0.0",
                entry_point="DirectAccess",
            )
        assert "DirectAccess" in str(exc_info.value)

    def test_empty_capability_identity_raises(self) -> None:
        """Empty capability identity raises InvalidBoundaryAccess."""
        with pytest.raises(InvalidBoundaryAccess):
            self.validator.validate_access(
                capability_identity="",
                capability_version="1.0.0",
            )

    def test_empty_capability_version_raises(self) -> None:
        """Empty capability version raises InvalidBoundaryAccess."""
        with pytest.raises(InvalidBoundaryAccess):
            self.validator.validate_access(
                capability_identity="text_generation",
                capability_version="",
            )

    def test_whitespace_identity_raises(self) -> None:
        """Whitespace-only identity raises InvalidBoundaryAccess."""
        with pytest.raises(InvalidBoundaryAccess):
            self.validator.validate_access(
                capability_identity="   ",
                capability_version="1.0.0",
            )

    def test_unauthorized_entry_point_is_subclass_of_invalid_access(
        self,
    ) -> None:
        """UnauthorizedEntryPoint is a specialized InvalidBoundaryAccess."""
        assert issubclass(UnauthorizedEntryPoint, InvalidBoundaryAccess)
