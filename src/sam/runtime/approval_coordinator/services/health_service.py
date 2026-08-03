"""Health Service for Approval Coordinator.

Maps lifecycle states to health status:
- UNINITIALIZED → UNAVAILABLE
- INITIALIZING   → DEGRADED
- RUNNING        → AVAILABLE
- STOPPING       → DEGRADED
- STOPPED        → UNAVAILABLE
"""

from enum import Enum
from typing import Dict, Any

from src.sam.runtime.approval_coordinator.lifecycle.coordinator_lifecycle import (
    CoordinatorLifecycleState,
    ApprovalCoordinatorLifecycle,
)


class HealthStatus(str, Enum):
    """Health status levels."""
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


# Health mapping
_HEALTH_MAP: Dict[CoordinatorLifecycleState, HealthStatus] = {
    CoordinatorLifecycleState.UNINITIALIZED: HealthStatus.UNAVAILABLE,
    CoordinatorLifecycleState.INITIALIZING: HealthStatus.DEGRADED,
    CoordinatorLifecycleState.RUNNING: HealthStatus.AVAILABLE,
    CoordinatorLifecycleState.STOPPING: HealthStatus.DEGRADED,
    CoordinatorLifecycleState.STOPPED: HealthStatus.UNAVAILABLE,
}


class HealthService:
    """Provides health status for the Approval Coordinator.

    Deterministic — same lifecycle state always maps to same health.
    """

    @staticmethod
    def get_health(lifecycle: ApprovalCoordinatorLifecycle) -> Dict[str, Any]:
        """Get current health status.

        Returns a dict with:
        - status: HealthStatus value
        - lifecycle_state: current lifecycle state
        - operational: whether the coordinator is operational
        """
        status = _HEALTH_MAP.get(lifecycle.state, HealthStatus.UNAVAILABLE)
        return {
            "status": status.value,
            "lifecycle_state": lifecycle.state.value,
            "operational": lifecycle.is_operational(),
            "terminal": lifecycle.is_terminal(),
        }
