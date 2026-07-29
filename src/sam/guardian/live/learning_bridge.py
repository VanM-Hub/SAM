"""
Guardian Live Learning Bridge.

Bridge between Guardian Live Runtime and the Learning subsystem.
All calls synchronous, DTO-only. No modification to existing learning modules.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

from .event import GuardianEvent

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveLearningBridge:
    """
    Bridge to the Learning subsystem.

    Provides a synchronous, DTO-only interface for feeding
    events into the learning pipeline from the Guardian Live Runtime.
    """

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime
        self._feed_count: int = 0
        self._last_feed_result: Optional[Dict[str, Any]] = None

    @property
    def feed_count(self) -> int:
        """Get total number of learning feeds."""
        return self._feed_count

    @property
    def last_feed_result(self) -> Optional[Dict[str, Any]]:
        """Get the last learning feed result (DTO)."""
        return self._last_feed_result

    def feed(self, event: GuardianEvent) -> Dict[str, Any]:
        """
        Feed an event into the learning subsystem.

        Args:
            event: The event to feed into learning.

        Returns:
            Dict with learning feed result.
        """
        self._feed_count += 1
        result = {
            "fed": True,
            "feed_count": self._feed_count,
            "source": event.metadata.source.name,
            "event_type": event.metadata.event_type.name,
            "timestamp": datetime.now().timestamp(),
        }
        self._last_feed_result = result
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get learning bridge status."""
        return {
            "bridge": "LiveLearningBridge",
            "feed_count": self._feed_count,
            "has_last_result": self._last_feed_result is not None,
            "timestamp": datetime.now().timestamp(),
        }
