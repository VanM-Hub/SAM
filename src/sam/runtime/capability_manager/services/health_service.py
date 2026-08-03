"""Capability Manager health service.

Reports the operational health of the Capability Manager unit.

Authority: R4-001 | R5-001 §2.2
"""

from sam.runtime.capability_manager.lifecycle.manager_lifecycle import (
    ManagerLifecycle,
    ManagerLifecycleState,
)


class HealthService:
    """Reports Capability Manager health status.

    Health is derived from the Manager's own lifecycle state.
    """

    _STATE_HEALTH_MAP = {
        ManagerLifecycleState.UNINITIALIZED: "unavailable",
        ManagerLifecycleState.INITIALIZING: "degraded",
        ManagerLifecycleState.RUNNING: "available",
        ManagerLifecycleState.STOPPING: "degraded",
        ManagerLifecycleState.STOPPED: "unavailable",
    }

    def __init__(self, lifecycle: ManagerLifecycle = None) -> None:
        self._lifecycle = lifecycle or ManagerLifecycle()

    @property
    def lifecycle(self) -> ManagerLifecycle:
        """The manager's lifecycle instance."""
        return self._lifecycle

    def get_health(self) -> str:
        """Report current health status.

        Returns:
            'available', 'degraded', or 'unavailable'.
        """
        return self._STATE_HEALTH_MAP.get(
            self._lifecycle.state, "unavailable"
        )
