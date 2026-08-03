"""HealthService — lifecycle state to health mapping.

Authority: I2-004 §4.6
"""

from sam.runtime.contract_enforcer.lifecycle.enforcer_lifecycle import (
    ContractEnforcerLifecycleState,
)

# Health mapping per lifecycle state
_HEALTH_MAP = {
    ContractEnforcerLifecycleState.UNINITIALIZED: "unavailable",
    ContractEnforcerLifecycleState.INITIALIZING: "degraded",
    ContractEnforcerLifecycleState.RUNNING: "available",
    ContractEnforcerLifecycleState.STOPPING: "degraded",
    ContractEnforcerLifecycleState.STOPPED: "unavailable",
}


class HealthService:
    """Maps lifecycle state to health string."""

    @staticmethod
    def get_health(state: ContractEnforcerLifecycleState) -> str:
        """Return health status for a lifecycle state."""
        return _HEALTH_MAP.get(state, "unknown")
