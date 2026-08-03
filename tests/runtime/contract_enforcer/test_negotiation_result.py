"""Tests for NegotiationResult model.

Authority: I2-004 §4
"""

from sam.runtime.contract_enforcer import (
    NegotiationResult,
    NegotiationStatus,
)


class TestNegotiationResult:
    """Tests for NegotiationResult model."""

    def test_resolved_factory(self) -> None:
        """resolved() factory creates RESOLVED result."""
        result = NegotiationResult.resolved(
            contract_id="memory.contract",
            version="1.0.0",
        )
        assert result.status == NegotiationStatus.RESOLVED
        assert result.negotiated_contract_id == "memory.contract"
        assert result.negotiated_version == "1.0.0"

    def test_deprecated_only_factory(self) -> None:
        """deprecated_only() factory creates DEPRECATED_ONLY result."""
        result = NegotiationResult.deprecated_only(
            contract_id="memory.contract",
            version="1.0.0",
        )
        assert result.status == NegotiationStatus.DEPRECATED_ONLY
        assert result.negotiated_version == "1.0.0"

    def test_no_intersection_factory(self) -> None:
        """no_intersection() factory creates NO_INTERSECTION result."""
        result = NegotiationResult.no_intersection()
        assert result.status == NegotiationStatus.NO_INTERSECTION
        assert result.negotiated_contract_id is None

    def test_no_compatible_factory(self) -> None:
        """no_compatible() factory creates NO_COMPATIBLE result."""
        result = NegotiationResult.no_compatible("No match")
        assert result.status == NegotiationStatus.NO_COMPATIBLE

    def test_is_success_resolved(self) -> None:
        """RESOLVED is success."""
        result = NegotiationResult.resolved("x", "1.0.0")
        assert result.is_success() is True
        assert result.is_failed() is False

    def test_is_success_deprecated_only(self) -> None:
        """DEPRECATED_ONLY is success (version agreed, with warning)."""
        result = NegotiationResult.deprecated_only("x", "1.0.0")
        assert result.is_success() is True

    def test_is_failed_no_intersection(self) -> None:
        """NO_INTERSECTION is failed."""
        result = NegotiationResult.no_intersection()
        assert result.is_failed() is True
        assert result.is_success() is False

    def test_is_failed_no_compatible(self) -> None:
        """NO_COMPATIBLE is failed."""
        result = NegotiationResult.no_compatible()
        assert result.is_failed() is True

    def test_frozen_immutability(self) -> None:
        """NegotiationResult is frozen."""
        result = NegotiationResult.resolved("x", "1.0.0")
        import pytest
        with pytest.raises(Exception):
            result.status = NegotiationStatus.FAILED  # type: ignore[misc]
