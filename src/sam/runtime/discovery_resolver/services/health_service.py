"""Health service for Discovery Resolver.

Maps ResolverLifecycleState to health status string.

Authority: I0-001 §2.3
"""

from sam.runtime.discovery_resolver.lifecycle.resolver_lifecycle import (
    ResolverLifecycle,
    ResolverLifecycleState,
)


class HealthService:
    """Maps operational lifecycle state to health status.

    Mapping:
        UNINITIALIZED → 'unavailable'
        INITIALIZING  → 'degraded'
        RUNNING       → 'available'
        STOPPING      → 'degraded'
        STOPPED       → 'unavailable'
    """

    _STATE_TO_HEALTH = {
        ResolverLifecycleState.UNINITIALIZED: "unavailable",
        ResolverLifecycleState.INITIALIZING: "degraded",
        ResolverLifecycleState.RUNNING: "available",
        ResolverLifecycleState.STOPPING: "degraded",
        ResolverLifecycleState.STOPPED: "unavailable",
    }

    def __init__(self, lifecycle: ResolverLifecycle) -> None:
        """Initialize with a ResolverLifecycle instance.

        Args:
            lifecycle: The resolver lifecycle to observe.
        """
        self._lifecycle = lifecycle

    def get_health(self) -> str:
        """Report current health status.

        Returns:
            'available', 'degraded', or 'unavailable'.
        """
        return self._STATE_TO_HEALTH.get(
            self._lifecycle.state,
            "unavailable",
        )
