"""Construction test for Discovery Resolver.

Verifies:
    - Discovery Resolver can be instantiated independently.
    - No dependency on capability_manager, citizen_host, or other units.
    - Basic resolution works after construction.

Authority: I2-003 §4 | I2-003 Container Contract
"""

from sam.runtime.discovery_resolver import (
    DiscoveryResolver,
    CapabilityRequest,
    ResolutionStatus,
    RegistryEntry,
    ResolverLifecycleState,
)


class TestConstruction:
    """Tests for Discovery Resolver construction."""

    def test_instantiate_without_any_external_deps(self) -> None:
        """Can instantiate DiscoveryResolver without any cross-unit imports."""
        resolver = DiscoveryResolver()
        assert resolver is not None

    def test_initial_health_is_unavailable(self) -> None:
        """Fresh resolver reports 'unavailable' health."""
        resolver = DiscoveryResolver()
        assert resolver.get_health() == "unavailable"

    def test_registry_starts_empty(self) -> None:
        """Fresh resolver has empty registry."""
        resolver = DiscoveryResolver()
        assert len(resolver.list_entries()) == 0

    def test_full_lifecycle_basic_resolution(self) -> None:
        """Construction → lifecycle start → register → resolve → result."""
        resolver = DiscoveryResolver()

        # Start lifecycle
        resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)
        assert resolver.get_health() == "available"

        # Register entries (simulating Capability Manager publication)
        resolver.register_entry(
            RegistryEntry("memory.lookup", "Memory", "1.0.0")
        )
        resolver.register_entry(
            RegistryEntry("memory.lookup", "Memory", "1.5.0")
        )
        resolver.register_entry(
            RegistryEntry("knowledge.search", "Knowledge", "1.0.0")
        )

        assert len(resolver.list_entries()) == 3

        # Exact match
        result = resolver.resolve(
            CapabilityRequest("memory.lookup", "1.0.0", "test")
        )
        assert result.status == ResolutionStatus.FOUND
        assert result.descriptor.version == "1.0.0"

        # Compatible fallback
        result2 = resolver.resolve(
            CapabilityRequest("memory.lookup", "1.3.0", "test")
        )
        assert result2.status == ResolutionStatus.FOUND
        assert result2.descriptor.version == "1.0.0"

        # Not found
        result3 = resolver.resolve(
            CapabilityRequest("nonexistent", "1.0.0", "test")
        )
        assert result3.status == ResolutionStatus.NOT_FOUND

    def test_construction_independent_of_capability_manager(self) -> None:
        """Can construct WITHOUT importing from capability_manager."""
        # This test verifies architectural independence.
        # No import from sam.runtime.capability_manager anywhere.
        resolver = DiscoveryResolver()
        resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)

        entry = RegistryEntry("test.cap", "Test", "1.0.0")
        resolver.register_entry(entry)

        result = resolver.resolve(
            CapabilityRequest("test.cap", "1.0.0", "test")
        )
        assert result.status == ResolutionStatus.FOUND
