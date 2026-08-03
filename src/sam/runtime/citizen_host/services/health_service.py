"""Citizen Host health service.

R9: Expose health.
Computes the health status of the Runtime based on lifecycle state.

Authority: GOVERNANCE | R4-001 §3.1 | R5-001 §2.1
"""

from sam.runtime.citizen_host.models.health import HealthStatus
from sam.runtime.citizen_host.lifecycle.host_lifecycle import HostLifecycleState


class HealthService:
    """Computes and reports Runtime health status.

    Health is derived from the HostLifecycle state:
        - RUNNING → AVAILABLE
        - DEGRADED → DEGRADED
        - INITIALIZING, STOPPING → DEGRADED
        - STOPPED, UNINITIALIZED → UNAVAILABLE
    """

    # ── State → Health mapping ────────────────────────────────────

    _STATE_HEALTH_MAP = {
        HostLifecycleState.UNINITIALIZED: HealthStatus.UNAVAILABLE,
        HostLifecycleState.INITIALIZING: HealthStatus.DEGRADED,
        HostLifecycleState.RUNNING: HealthStatus.AVAILABLE,
        HostLifecycleState.DEGRADED: HealthStatus.DEGRADED,
        HostLifecycleState.STOPPING: HealthStatus.DEGRADED,
        HostLifecycleState.STOPPED: HealthStatus.UNAVAILABLE,
    }

    def compute_health(self, state: HostLifecycleState) -> HealthStatus:
        """Compute health status from lifecycle state.

        Deterministic: same state always returns same health status.

        Args:
            state: Current HostLifecycleState.

        Returns:
            HealthStatus corresponding to the lifecycle state.
        """
        return self._STATE_HEALTH_MAP.get(state, HealthStatus.UNAVAILABLE)
