"""Audit Recorder Health Service.

Provides health reporting for the Audit Recorder.
Maps lifecycle state to health status.
"""

from typing import Any, Dict, Optional

from ..lifecycle.recorder_lifecycle import RecorderLifecycleState


class HealthService:
    """Reports health status for the Audit Recorder.

    Health status mappings:
    - UNINITIALIZED → UNAVAILABLE
    - INITIALIZING → DEGRADED
    - RUNNING → HEALTHY
    - STOPPING → DEGRADED
    - STOPPED → UNAVAILABLE
    """

    def __init__(self, lifecycle_getter=None, record_count_getter=None):
        """Initialize with callbacks for state and count.

        Args:
            lifecycle_getter: Callable returning current RecorderLifecycleState.
            record_count_getter: Callable returning total record count.
        """
        self._lifecycle_getter = lifecycle_getter
        self._record_count_getter = record_count_getter

    def get_health(self) -> Dict[str, Any]:
        """Return current health report."""
        lifecycle = self._get_lifecycle()
        record_count = self._get_record_count()

        health_status = self._map_lifecycle_to_health(lifecycle)

        return {
            "status": health_status,
            "lifecycle": lifecycle.value if lifecycle else "unknown",
            "record_count": record_count if record_count is not None else 0,
            "unit": "audit_recorder",
            "role": "terminal",
        }

    def _get_lifecycle(self) -> Optional[RecorderLifecycleState]:
        """Get current lifecycle state via callback."""
        if self._lifecycle_getter:
            return self._lifecycle_getter()
        return None

    def _get_record_count(self) -> Optional[int]:
        """Get current record count via callback."""
        if self._record_count_getter:
            return self._record_count_getter()
        return None

    @staticmethod
    def _map_lifecycle_to_health(
        lifecycle: Optional[RecorderLifecycleState],
    ) -> str:
        """Map lifecycle state to health status string."""
        if lifecycle is None:
            return "UNKNOWN"
        mapping = {
            RecorderLifecycleState.UNINITIALIZED: "UNAVAILABLE",
            RecorderLifecycleState.INITIALIZING: "DEGRADED",
            RecorderLifecycleState.RUNNING: "HEALTHY",
            RecorderLifecycleState.STOPPING: "DEGRADED",
            RecorderLifecycleState.STOPPED: "UNAVAILABLE",
        }
        return mapping.get(lifecycle, "UNKNOWN")
