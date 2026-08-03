"""Health Service for Execution Scheduler.

Maps scheduler lifecycle state to health status:
- RUNNING → available
- INITIALIZING/STOPPING → degraded
- UNINITIALIZED/STOPPED → unavailable
"""

from typing import Any, Dict

from src.sam.runtime.execution_scheduler.lifecycle.scheduler_lifecycle import (
    SchedulerLifecycleState,
    SchedulerLifecycle,
)


class HealthService:
    """Maps lifecycle state to health status."""

    STATUS_MAP = {
        SchedulerLifecycleState.UNINITIALIZED: "unavailable",
        SchedulerLifecycleState.INITIALIZING: "degraded",
        SchedulerLifecycleState.RUNNING: "available",
        SchedulerLifecycleState.STOPPING: "degraded",
        SchedulerLifecycleState.STOPPED: "unavailable",
    }

    def __init__(self, lifecycle: SchedulerLifecycle):
        self._lifecycle = lifecycle

    def get_health(self) -> Dict[str, Any]:
        """Return health status dict."""
        state = self._lifecycle.state
        return {
            "status": self.STATUS_MAP.get(state, "unknown"),
            "lifecycle_state": state.value,
            "operational": self._lifecycle.is_operational(),
            "terminal": self._lifecycle.is_terminal(),
        }

    def is_available(self) -> bool:
        """Check if the scheduler is available for operations."""
        return self._lifecycle.is_operational()
