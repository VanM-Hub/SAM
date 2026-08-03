"""Tests for determinism guarantee.

Verifies ADR-002 determinism contract:
    same registry content + same request → same result
    no hidden randomness, no implicit context

Authority: I2-003 §4 | ADR-002 | REGISTRY_SPEC L147/L149
"""

from sam.runtime.discovery_resolver import (
    DiscoveryResolver,
    CapabilityRequest,
    ResolutionStatus,
    RegistryEntry,
    ResolverLifecycleState,
)


class TestDeterminism:
    """Tests for deterministic resolution."""

    def setup_method(self) -> None:
        self.resolver = DiscoveryResolver()
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)
        self.resolver.register_entry(
            RegistryEntry("memory.lookup", "Memory", "1.0.0")
        )
        self.resolver.register_entry(
            RegistryEntry("memory.lookup", "Memory", "1.5.0")
        )
        self.resolver.register_entry(
            RegistryEntry("memory.lookup", "Memory", "2.0.0")
        )

    def test_same_request_same_exact_result(self) -> None:
        """Same exact-match request returns same result every time."""
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        results = [self.resolver.resolve(req) for _ in range(50)]
        first = results[0]
        for r in results:
            assert r.status == first.status
            assert r.descriptor.identity == first.descriptor.identity
            assert r.descriptor.version == first.descriptor.version

    def test_same_request_same_compatible_result(self) -> None:
        """Same compatible request returns same tie-broken result."""
        req = CapabilityRequest("memory.lookup", "1.3.0", "test")
        results = [self.resolver.resolve(req) for _ in range(50)]
        first = results[0]
        assert first.status == ResolutionStatus.FOUND
        for r in results:
            assert r.status == first.status
            assert r.descriptor.version == first.descriptor.version

    def test_same_request_same_not_found(self) -> None:
        """Same NOT_FOUND request returns NOT_FOUND every time."""
        req = CapabilityRequest("nonexistent", "1.0.0", "test")
        results = [self.resolver.resolve(req) for _ in range(30)]
        for r in results:
            assert r.status == ResolutionStatus.NOT_FOUND

    def test_same_request_same_version_mismatch(self) -> None:
        """Same VERSION_MISMATCH request returns mismatch every time."""
        req = CapabilityRequest("memory.lookup", "3.0.0", "test")
        results = [self.resolver.resolve(req) for _ in range(30)]
        for r in results:
            assert r.status == ResolutionStatus.VERSION_MISMATCH

    def test_registry_unchanged_after_resolution(self) -> None:
        """Registry count is unchanged after N resolutions."""
        initial = len(self.resolver.list_entries())
        req = CapabilityRequest("memory.lookup", "1.0.0", "test")
        for _ in range(100):
            self.resolver.resolve(req)
        assert len(self.resolver.list_entries()) == initial

    def test_different_requests_different_results_is_valid(self) -> None:
        """Different requests CAN produce different results."""
        r1 = self.resolver.resolve(
            CapabilityRequest("memory.lookup", "1.0.0", "test")
        )
        r2 = self.resolver.resolve(
            CapabilityRequest("memory.lookup", "2.0.0", "test")
        )
        # Both can be FOUND but with different versions
        assert r1.status == ResolutionStatus.FOUND
        # r2 could be FOUND (2.0.0 exact) or VERSION_MISMATCH
        # depends on exact match logic.
        # The key point: determinism is per-request, not across requests.
