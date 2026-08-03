"""Tests for Citizen Host domain models — BoundedCapabilityDomain.

Verifies model integrity, field validation, immutability.

Authority: I2-001 §6.2
"""

import pytest

from sam.runtime.citizen_host import BoundedCapabilityDomain


class TestBoundedCapabilityDomain:
    """Tests for BoundedCapabilityDomain model."""

    def test_create_domain_with_required_fields(self) -> None:
        """Domain can be created with identity and display_name."""
        domain = BoundedCapabilityDomain(
            identity="com.example.runtime",
            display_name="Example Runtime",
        )
        assert domain.identity == "com.example.runtime"
        assert domain.display_name == "Example Runtime"
        assert domain.version == "1.0.0"

    def test_create_domain_with_description(self) -> None:
        """Domain accepts optional description."""
        domain = BoundedCapabilityDomain(
            identity="com.example.runtime",
            display_name="Example Runtime",
            description="An example runtime for testing",
        )
        assert domain.description == "An example runtime for testing"

    def test_validate_with_non_empty_identity(self) -> None:
        """Domain with non-empty identity passes validation."""
        domain = BoundedCapabilityDomain(
            identity="com.example.runtime",
            display_name="Example",
        )
        assert domain.validate() is True

    def test_validate_with_empty_identity(self) -> None:
        """Domain with empty identity fails validation."""
        domain = BoundedCapabilityDomain(
            identity="",
            display_name="Example",
        )
        assert domain.validate() is False

    def test_domain_is_frozen(self) -> None:
        """BoundedCapabilityDomain is immutable (frozen dataclass)."""
        domain = BoundedCapabilityDomain(
            identity="com.example.runtime",
            display_name="Example",
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            domain.identity = "changed"  # type: ignore[misc]

    def test_repr_includes_identity_and_version(self) -> None:
        """String representation includes key fields."""
        domain = BoundedCapabilityDomain(
            identity="com.example.runtime",
            display_name="Example",
            version="2.0.0",
        )
        repr_str = repr(domain)
        assert "com.example.runtime" in repr_str
        assert "2.0.0" in repr_str

    def test_default_version_is_1_0_0(self) -> None:
        """Default version is 1.0.0."""
        domain = BoundedCapabilityDomain(
            identity="com.example.runtime",
            display_name="Example",
        )
        assert domain.version == "1.0.0"
