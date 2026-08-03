"""Tests for CompatibilityResult model.

Authority: I2-004 §4 | CONTRACT_SPEC
"""

from sam.runtime.contract_enforcer import (
    CompatibilityResult,
    CompatibilityStatus,
)


class TestCompatibilityResult:
    """Tests for CompatibilityResult model."""

    def test_compatible_factory(self) -> None:
        """compatible() factory creates COMPATIBLE result."""
        result = CompatibilityResult.compatible(
            predecessor_id="v1", successor_id="v2",
        )
        assert result.status == CompatibilityStatus.COMPATIBLE
        assert result.is_compatible is True
        assert result.backward_compatible is True
        assert result.forward_compatible is True

    def test_breaking_factory(self) -> None:
        """breaking() factory creates BREAKING result."""
        result = CompatibilityResult.breaking(
            changes=["Removed field X"],
            predecessor_id="v1",
            successor_id="v2",
        )
        assert result.status == CompatibilityStatus.BREAKING
        assert result.is_compatible is False
        assert result.backward_compatible is False
        assert result.forward_compatible is False
        assert "Removed field X" in result.reason

    def test_unknown_factory(self) -> None:
        """unknown() factory creates UNKNOWN result."""
        result = CompatibilityResult.unknown("Cannot determine")
        assert result.status == CompatibilityStatus.UNKNOWN
        assert result.is_compatible is False
        assert "Cannot determine" in result.reason

    def test_breaking_changes_list(self) -> None:
        """Breaking changes list preserved."""
        changes = ["change1", "change2"]
        result = CompatibilityResult.breaking(changes=changes)
        assert len(result.breaking_changes) == 2

    def test_frozen_immutability(self) -> None:
        """CompatibilityResult is frozen."""
        result = CompatibilityResult.compatible()
        import pytest
        with pytest.raises(Exception):
            result.status = CompatibilityStatus.BREAKING  # type: ignore[misc]
