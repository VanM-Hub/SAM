"""
Guardian Live Execution Bridge.

Bridge between Guardian Live Runtime and the Execution Preview subsystem.
All calls synchronous, DTO-only. Preview only — no auto execution.
No modification to existing execution modules.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

from .event import GuardianEvent

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveExecutionBridge:
    """
    Bridge to the Execution Preview subsystem.

    Provides a synchronous, DTO-only interface for generating
    execution previews from events. Preview only — does NOT execute.
    """

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime
        self._preview_count: int = 0
        self._last_preview_result: Optional[Dict[str, Any]] = None

    @property
    def preview_count(self) -> int:
        """Get total number of execution previews."""
        return self._preview_count

    @property
    def last_preview_result(self) -> Optional[Dict[str, Any]]:
        """Get the last execution preview result (DTO)."""
        return self._last_preview_result

    def preview(self, event: GuardianEvent) -> Dict[str, Any]:
        """
        Generate an execution preview based on an event.

        Preview only — does NOT execute any action.

        Args:
            event: The event to generate a preview for.

        Returns:
            Dict with execution preview result.
        """
        self._preview_count += 1
        result = {
            "previewed": True,
            "preview_count": self._preview_count,
            "source": event.metadata.source.name,
            "event_type": event.metadata.event_type.name,
            "preview_only": True,
            "timestamp": datetime.now().timestamp(),
        }
        self._last_preview_result = result
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get execution bridge status."""
        return {
            "bridge": "LiveExecutionBridge",
            "preview_count": self._preview_count,
            "has_last_result": self._last_preview_result is not None,
            "timestamp": datetime.now().timestamp(),
        }
