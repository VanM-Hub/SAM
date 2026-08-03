"""Tests for CapabilityRequest model.

Authority: I2-003 §4
"""

import pytest

from sam.runtime.discovery_resolver import (
    CapabilityRequest,
)


class TestCapabilityRequest:
    """Tests for CapabilityRequest — frozen, immutable representation
    of a capability resolution request."""

    def test_create_with_required_fields(self) -> None:
        """Can create with identity, version, requester."""
        req = CapabilityRequest("memory.lookup", "1.0.0", "citizen-001")
        assert req.identity == "memory.lookup"
        assert req.requested_version == "1.0.0"
        assert req.requester == "citizen-001"

    def test_validate_valid_request(self) -> None:
        """validate() returns True for a complete request."""
        req = CapabilityRequest("memory.lookup", "1.0.0", "citizen-001")
        assert req.validate() is True

    def test_validate_empty_identity(self) -> None:
        """validate() returns False for empty identity."""
        req = CapabilityRequest("", "1.0.0", "citizen-001")
        assert req.validate() is False

    def test_validate_empty_version(self) -> None:
        """validate() returns False for empty version."""
        req = CapabilityRequest("memory.lookup", "", "citizen-001")
        assert req.validate() is False

    def test_validate_empty_requester(self) -> None:
        """validate() returns False for empty requester."""
        req = CapabilityRequest("memory.lookup", "1.0.0", "")
        assert req.validate() is False

    def test_validate_whitespace_only(self) -> None:
        """validate() returns False for whitespace-only fields."""
        req = CapabilityRequest("  ", "1.0.0", "citizen-001")
        assert req.validate() is False

    def test_major_version_from_standard(self) -> None:
        """major_version() extracts the major component."""
        req = CapabilityRequest("x", "3.2.1", "y")
        assert req.major_version() == 3

    def test_major_version_from_zero(self) -> None:
        """major_version() extracts major=0."""
        req = CapabilityRequest("x", "0.9.5", "y")
        assert req.major_version() == 0

    def test_major_version_from_invalid(self) -> None:
        """major_version() returns 0 for unparseable versions."""
        req = CapabilityRequest("x", "abc", "y")
        assert req.major_version() == 0

    def test_frozen_immutability(self) -> None:
        """CapabilityRequest is frozen (immutable)."""
        req = CapabilityRequest("memory.lookup", "1.0.0", "citizen-001")
        with pytest.raises(Exception):
            req.identity = "changed"  # type: ignore[misc]

    def test_repr_contains_key_info(self) -> None:
        """repr includes identity and version."""
        req = CapabilityRequest("memory.lookup", "2.0.0", "citizen-001")
        r = repr(req)
        assert "memory.lookup" in r
        assert "2.0.0" in r
