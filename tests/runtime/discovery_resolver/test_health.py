"""Tests for HealthService — lifecycle state to health mapping.

Authority: I2-003 §4
"""

from sam.runtime.discovery_resolver import (
    DiscoveryResolver,
    ResolverLifecycleState,
)


class TestHealthService:
    """Tests for HealthService."""

    def setup_method(self) -> None:
        self.resolver = DiscoveryResolver()

    def test_uninitialized_is_unavailable(self) -> None:
        """UNINITIALIZED → 'unavailable'."""
        assert self.resolver.get_health() == "unavailable"

    def test_initializing_is_degraded(self) -> None:
        """INITIALIZING → 'degraded'."""
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        assert self.resolver.get_health() == "degraded"

    def test_running_is_available(self) -> None:
        """RUNNING → 'available'."""
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)
        assert self.resolver.get_health() == "available"

    def test_stopping_is_degraded(self) -> None:
        """STOPPING → 'degraded'."""
        self._goto_running()
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.STOPPING)
        assert self.resolver.get_health() == "degraded"

    def test_stopped_is_unavailable(self) -> None:
        """STOPPED → 'unavailable'."""
        self._goto_running()
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.STOPPING)
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.STOPPED)
        assert self.resolver.get_health() == "unavailable"

    def _goto_running(self) -> None:
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.INITIALIZING)
        self.resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)
