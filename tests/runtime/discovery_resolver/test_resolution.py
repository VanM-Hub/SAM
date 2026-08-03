"""Tests for ADR-002 Resolution Service.

Covers: exact match, compatible fallback, tie-break,
deprecated handling, version mismatch, not found.

Authority: I2-003 §4 | ADR-002 Decision
"""

import pytest

from sam.runtime.discovery_resolver import (
    DiscoveryResolver,
    CapabilityRequest,
    ResolutionStatus,
    RegistryEntry,
    ResolverLifecycleState,
)


def _entry(
    identity: str = "memory.lookup",
    version: str = "1.0.0",
    state: str = "AVAILABLE",
) -> RegistryEntry:
    return RegistryEntry(
        identity=identity,
        name="Test Capability",
        version=version,
        lifecycle_state=state,
        contract_reference=f"contract://{identity}/{version}",
    )


class TestExactMatch:
    """Tests for exact match resolution."""

    def setup_method(self) -> None:
        self.resolver = DiscoveryResolver()
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)

    def test_exact_match_found(self) -> None:
        """Exact identity + version match → FOUND."""
        self.resolver.register_entry(_entry("memory.lookup", "1.0.0"))
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.FOUND
        assert result.descriptor.identity == "memory.lookup"
        assert result.descriptor.version == "1.0.0"

    def test_exact_match_with_multiple_entries(self) -> None:
        """Only exact match returned when multiple entries exist."""
        self.resolver.register_entry(_entry("memory.lookup", "1.0.0"))
        self.resolver.register_entry(_entry("memory.lookup", "1.1.0"))
        self.resolver.register_entry(_entry("memory.lookup", "2.0.0"))
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.FOUND
        assert result.descriptor.version == "1.0.0"

    def test_not_found_wrong_identity(self) -> None:
        """Different identity → NOT_FOUND."""
        self.resolver.register_entry(_entry("memory.lookup", "1.0.0"))
        req = CapabilityRequest("knowledge.search", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.NOT_FOUND

    def test_exact_match_excluded_suspended(self) -> None:
        """SUSPENDED exact match → NOT_FOUND."""
        self.resolver.register_entry(
            _entry("memory.lookup", "1.0.0", state="SUSPENDED")
        )
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.NOT_FOUND

    def test_exact_match_excluded_removed(self) -> None:
        """REMOVED exact match → NOT_FOUND."""
        self.resolver.register_entry(
            _entry("memory.lookup", "1.0.0", state="REMOVED")
        )
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.NOT_FOUND

    def test_exact_match_deprecated_only(self) -> None:
        """DEPRECATED exact match → DEPRECATED_ONLY."""
        self.resolver.register_entry(
            _entry("memory.lookup", "1.0.0", state="DEPRECATED")
        )
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.DEPRECATED_ONLY
        assert result.descriptor is not None


class TestCompatibleFallback:
    """Tests for compatible (same major) fallback."""

    def setup_method(self) -> None:
        self.resolver = DiscoveryResolver()
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)

    def test_compatible_fallback_same_major(self) -> None:
        """No exact → same major version → FOUND (compatible)."""
        self.resolver.register_entry(_entry("memory.lookup", "1.5.0"))
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.FOUND
        assert result.descriptor.version == "1.5.0"

    def test_compatible_prefers_non_deprecated(self) -> None:
        """Compatible non-deprecated preferred over deprecated."""
        self.resolver.register_entry(
            _entry("memory.lookup", "1.1.0", state="DEPRECATED")
        )
        self.resolver.register_entry(
            _entry("memory.lookup", "1.5.0", state="AVAILABLE")
        )
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.FOUND
        assert result.descriptor.version == "1.5.0"

    def test_compatible_only_deprecated(self) -> None:
        """Only deprecated compatible → DEPRECATED_ONLY."""
        self.resolver.register_entry(
            _entry("memory.lookup", "1.1.0", state="DEPRECATED")
        )
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.DEPRECATED_ONLY
        assert result.descriptor.version == "1.1.0"

    def test_version_mismatch_different_major(self) -> None:
        """Different major version → VERSION_MISMATCH."""
        self.resolver.register_entry(_entry("memory.lookup", "2.0.0"))
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.VERSION_MISMATCH


class TestTieBreak:
    """Tests for deterministic tie-break."""

    def setup_method(self) -> None:
        self.resolver = DiscoveryResolver()
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)

    def test_tie_break_by_version_when_multiple_compatible(self) -> None:
        """Multiple compatible → deterministic version sort."""
        self.resolver.register_entry(_entry("memory.lookup", "1.9.0"))
        self.resolver.register_entry(_entry("memory.lookup", "1.2.0"))
        self.resolver.register_entry(_entry("memory.lookup", "1.5.0"))
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.descriptor.version == "1.2.0"  # sorted: "1.2.0" < "1.5.0" < "1.9.0"

    def test_tie_break_by_identity_when_multiple_capabilities(self) -> None:
        """Multiple identities → deterministic identity sort."""
        self.resolver.register_entry(_entry("memory.lookup", "1.0.0"))
        self.resolver.register_entry(_entry("knowledge.search", "1.0.0"))
        req = CapabilityRequest("knowledge.search", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.FOUND
        assert result.descriptor.identity == "knowledge.search"


class TestEdgeCases:
    """Tests for edge cases."""

    def setup_method(self) -> None:
        self.resolver = DiscoveryResolver()
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)

    def test_empty_registry_returns_not_found(self) -> None:
        """Empty registry → NOT_FOUND."""
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.NOT_FOUND

    def test_resolve_exact_helper(self) -> None:
        """resolve_exact finds exact match."""
        self.resolver.register_entry(_entry("memory.lookup", "1.0.0"))
        found = self.resolver.resolve_exact("memory.lookup", "1.0.0")
        assert found is not None
        assert found.version == "1.0.0"

    def test_resolve_exact_missing(self) -> None:
        """resolve_exact returns None for missing."""
        assert self.resolver.resolve_exact("nonexistent", "1.0.0") is None

    def test_resolve_compatible_returns_list(self) -> None:
        """resolve_compatible returns sorted list."""
        self.resolver.register_entry(_entry("memory.lookup", "1.5.0"))
        self.resolver.register_entry(_entry("memory.lookup", "1.1.0"))
        result = self.resolver.resolve_compatible("memory.lookup", 1)
        assert len(result) == 2
        assert result[0].version == "1.1.0"

    def test_is_success_and_is_fatal(self) -> None:
        """ResolutionResult.is_success() and is_fatal() behave correctly."""
        self.resolver.register_entry(_entry("memory.lookup", "1.0.0"))
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.is_success() is True
        assert result.is_fatal() is False

        req2 = CapabilityRequest("nonexistent", "1.0.0", "test")
        result2 = self.resolver.resolve(req2)
        assert result2.is_success() is False
        assert result2.is_fatal() is True

    def test_suspended_in_compatible_is_excluded(self) -> None:
        """SUSPENDED compatible candidate excluded."""
        self.resolver.register_entry(
            _entry("memory.lookup", "1.5.0", state="SUSPENDED")
        )
        self.resolver.register_entry(
            _entry("memory.lookup", "1.3.0", state="AVAILABLE")
        )
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert result.status == ResolutionStatus.FOUND
        assert result.descriptor.version == "1.3.0"

    def test_resolution_produces_reason(self) -> None:
        """ResolutionResult always has a reason string."""
        self.resolver.register_entry(_entry("memory.lookup", "1.0.0"))
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        result = self.resolver.resolve(req)
        assert len(result.reason) > 0
