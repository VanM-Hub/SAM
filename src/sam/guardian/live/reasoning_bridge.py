"""
Guardian Live Reasoning Bridge.

Bridge between Guardian Live Runtime and the Reasoning subsystem.
All calls synchronous, DTO-only. No modification to existing reasoning modules.
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime

from .event import GuardianEvent

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveReasoningBridge:
    """
    Bridge to the Reasoning subsystem.

    Provides a synchronous, DTO-only interface for triggering
    reasoning cycles from the Guardian Live Runtime.
    """

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime
        self._trigger_count: int = 0
        self._last_reasoning_result: Optional[Dict[str, Any]] = None

    @property
    def trigger_count(self) -> int:
        """Get total number of reasoning triggers."""
        return self._trigger_count

    @property
    def last_reasoning_result(self) -> Optional[Dict[str, Any]]:
        """Get the last reasoning result (DTO)."""
        return self._last_reasoning_result

    def trigger(self, event: GuardianEvent) -> Dict[str, Any]:
        """
        Trigger a reasoning cycle based on an event.

        Args:
            event: The event that triggered reasoning.

        Returns:
            Dict with reasoning trigger result.
        """
        self._trigger_count += 1
        result = {
            "triggered": True,
            "trigger_count": self._trigger_count,
            "source": event.metadata.source.name,
            "event_type": event.metadata.event_type.name,
            "timestamp": datetime.now().timestamp(),
        }
        self._last_reasoning_result = result
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get reasoning bridge status."""
        return {
            "bridge": "LiveReasoningBridge",
            "trigger_count": self._trigger_count,
            "has_last_result": self._last_reasoning_result is not None,
            "timestamp": datetime.now().timestamp(),
        }
