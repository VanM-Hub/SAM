"""
Guardian Live Conversation Bridge.

Provides 10 DTO-only query methods for conversation integration.
All methods return frozen dicts. No async, no threading, no network.
No modification to existing Conversation API.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
from collections import defaultdict

from .event import (
    GuardianEvent,
    GuardianEventType,
    GuardianEventPriority,
    GuardianEventSource,
    GuardianEventSnapshot,
)
from .history import EventRecord

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveConversationBridge:
    """
    Bridge between Guardian Live Runtime and Conversation API.

    Provides 10 query methods:
        1. recent_events        - Last N events
        2. latest_alerts        - Most recent alert events
        3. event_history        - Filtered event history
        4. dispatcher_status    - Dispatcher statistics
        5. runtime_health       - Runtime health info
        6. subscriber_list      - Registered subscribers
        7. priority_statistics  - Event counts by priority
        8. last_event           - The most recent event
        9. event_snapshot       - Last dispatch snapshot
        10. live_summary        - Full runtime summary

    All methods return DTO dicts (frozen, no references).
    """

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime
        self._update_count: int = 0

    @property
    def query_count(self) -> int:
        """Get total number of query types available."""
        return 10

    def update(self) -> None:
        """Mark that an update occurred."""
        self._update_count += 1

    @property
    def update_count(self) -> int:
        """Get total number of updates performed."""
        return self._update_count

    def recent_events(self, count: int = 10) -> Dict[str, Any]:
        """
        Get the most recent N events.

        Args:
            count: Number of events to return.

        Returns:
            Dict with recent events and metadata.
        """
        records = self._runtime.history.get_all()
        recent = records[-count:] if count > 0 else []
        return {
            "query": "recent_events",
            "count": len(recent),
            "total": self._runtime.history.count,
            "timestamp": datetime.now().timestamp(),
            "events": [
                {
                    "event_id": r.event.event_id,
                    "type": r.event.metadata.event_type.name,
                    "source": r.event.metadata.source.name,
                    "priority": r.event.metadata.priority.name,
                    "dispatched_at": r.dispatched_at,
                    "processing_ms": r.processing_ms,
                }
                for r in recent
            ],
        }

    def latest_alerts(self, count: int = 10) -> Dict[str, Any]:
        """
        Get the most recent alert events.

        Args:
            count: Number of alerts to return.

        Returns:
            Dict with alert events.
        """
        records = self._runtime.history.filter(
            event_type=GuardianEventType.ALERT_RAISED,
            limit=count,
        )
        cleared = self._runtime.history.filter(
            event_type=GuardianEventType.ALERT_CLEARED,
            limit=count,
        )
        return {
            "query": "latest_alerts",
            "active_alerts": len(records),
            "cleared_alerts": len(cleared),
            "timestamp": datetime.now().timestamp(),
            "alerts": [
                {
                    "event_id": r.event.event_id,
                    "type": r.event.metadata.event_type.name,
                    "source": r.event.metadata.source.name,
                    "dispatched_at": r.dispatched_at,
                    "payload": str(r.event.payload),
                }
                for r in (records + cleared)[-count:]
            ],
        }

    def event_history(self, **filters) -> Dict[str, Any]:
        """
        Get filtered event history.

        Args:
            **filters: Filters passed to EventHistory.filter().

        Returns:
            Dict with filtered event history.
        """
        records = self._runtime.history.filter(**filters)
        return {
            "query": "event_history",
            "count": len(records),
            "filters": {k: str(v) for k, v in filters.items()},
            "timestamp": datetime.now().timestamp(),
            "records": [
                {
                    "event_id": r.event.event_id,
                    "type": r.event.metadata.event_type.name,
                    "source": r.event.metadata.source.name,
                    "priority": r.event.metadata.priority.name,
                    "dispatched_at": r.dispatched_at,
                    "processing_ms": r.processing_ms,
                    "errors": r.error_count,
                }
                for r in records
            ],
        }

    def dispatcher_status(self) -> Dict[str, Any]:
        """
        Get dispatcher statistics.

        Returns:
            Dict with dispatcher status.
        """
        dispatcher = self._runtime.dispatcher
        return {
            "query": "dispatcher_status",
            "timestamp": datetime.now().timestamp(),
            "subscriber_count": dispatcher.subscriber_count,
            "total_dispatched": dispatcher.total_dispatched,
            "error_count": dispatcher.error_count,
            "event_type_counts": dispatcher.get_event_counts_by_type(),
            "event_source_counts": dispatcher.get_event_counts_by_source(),
            "subscribers": dispatcher.get_subscriber_names(),
        }

    def runtime_health(self) -> Dict[str, Any]:
        """
        Get runtime health information.

        Returns:
            Dict with runtime health data.
        """
        status = self._runtime.get_status()
        stats = self._runtime.history.statistics
        return {
            "query": "runtime_health",
            "timestamp": datetime.now().timestamp(),
            "is_running": status["is_running"],
            "total_dispatched": status["total_dispatched"],
            "error_count": status["error_count"],
            "history_count": status["history_count"],
            "subscriber_count": status["subscriber_count"],
            "average_processing_ms": stats.average_processing_ms,
            "max_processing_ms": stats.max_processing_ms,
            "min_processing_ms": stats.min_processing_ms,
            "last_snapshot_completed": (
                self._runtime.last_snapshot.completed
                if self._runtime.last_snapshot
                else None
            ),
        }

    def subscriber_list(self) -> Dict[str, Any]:
        """
        Get list of registered subscribers.

        Returns:
            Dict with subscriber information.
        """
        subscribers = self._runtime.dispatcher.subscribers
        return {
            "query": "subscriber_list",
            "timestamp": datetime.now().timestamp(),
            "count": len(subscribers),
            "subscribers": [
                {
                    "name": s.get_name(),
                    "type": type(s).__name__,
                }
                for s in subscribers
            ],
        }

    def priority_statistics(self) -> Dict[str, Any]:
        """
        Get event counts grouped by priority.

        Returns:
            Dict with priority statistics.
        """
        stats = self._runtime.history.statistics
        return {
            "query": "priority_statistics",
            "timestamp": datetime.now().timestamp(),
            "total": stats.total_events,
            "priorities": stats.priorities,
            "statistics": stats.to_dict(),
        }

    def last_event(self) -> Dict[str, Any]:
        """
        Get the most recent event.

        Returns:
            Dict with the last event or empty state.
        """
        latest = self._runtime.history.latest
        if latest is None:
            return {
                "query": "last_event",
                "timestamp": datetime.now().timestamp(),
                "has_event": False,
                "event": None,
            }
        return {
            "query": "last_event",
            "timestamp": datetime.now().timestamp(),
            "has_event": True,
            "event": {
                "event_id": latest.event.event_id,
                "type": latest.event.metadata.event_type.name,
                "source": latest.event.metadata.source.name,
                "priority": latest.event.metadata.priority.name,
                "dispatched_at": latest.dispatched_at,
                "processing_ms": latest.processing_ms,
                "subscriber_count": latest.subscriber_count,
                "error_count": latest.error_count,
            },
        }

    def event_snapshot(self) -> Dict[str, Any]:
        """
        Get the last dispatch snapshot.

        Returns:
            Dict with snapshot data or empty state.
        """
        snapshot = self._runtime.last_snapshot
        if snapshot is None:
            return {
                "query": "event_snapshot",
                "timestamp": datetime.now().timestamp(),
                "has_snapshot": False,
                "snapshot": None,
            }
        return {
            "query": "event_snapshot",
            "timestamp": datetime.now().timestamp(),
            "has_snapshot": True,
            "snapshot": snapshot.to_dict(),
        }

    def live_summary(self) -> Dict[str, Any]:
        """
        Get a full runtime summary combining all key data.

        Returns:
            Dict with complete runtime summary.
        """
        return {
            "query": "live_summary",
            "timestamp": datetime.now().timestamp(),
            "runtime": self._runtime.get_status(),
            "last_event": (
                self.last_event().get("event")
            ),
            "statistics": self._runtime.history.statistics.to_dict(),
            "subscribers": [
                s.get_name()
                for s in self._runtime.dispatcher.subscribers
            ],
            "update_count": self._update_count,
        }
