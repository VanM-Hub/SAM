"""
Guardian Live Dashboard Bridge.

Provides 6 immutable dashboard cards for the live runtime.
All DTOs are frozen. No async, no threading, no network.
No modification to existing dashboard API.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from .event import (
    GuardianEventType,
    GuardianEventPriority,
    GuardianEventSource,
)

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


@dataclass(frozen=True)
class LiveRuntimeCard:
    """
    Immutable card showing live runtime status.
    """

    is_running: bool
    subscriber_count: int
    total_dispatched: int
    error_count: int
    history_count: int
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Live Runtime",
            "is_running": self.is_running,
            "subscriber_count": self.subscriber_count,
            "total_dispatched": self.total_dispatched,
            "error_count": self.error_count,
            "history_count": self.history_count,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class RecentEventsCard:
    """
    Immutable card showing recent event activity.
    """

    total_events: int
    events_by_type: Dict[str, int]
    events_by_source: Dict[str, int]
    events_by_priority: Dict[str, int]
    last_event_type: Optional[str]
    last_event_source: Optional[str]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Recent Events",
            "total_events": self.total_events,
            "events_by_type": dict(self.events_by_type),
            "events_by_source": dict(self.events_by_source),
            "events_by_priority": dict(self.events_by_priority),
            "last_event_type": self.last_event_type,
            "last_event_source": self.last_event_source,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class DispatchStatusCard:
    """
    Immutable card showing dispatch status.
    """

    subscriber_count: int
    total_dispatched: int
    error_count: int
    average_processing_ms: float
    last_snapshot_completed: bool
    subscriber_names: List[str]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Dispatch Status",
            "subscriber_count": self.subscriber_count,
            "total_dispatched": self.total_dispatched,
            "error_count": self.error_count,
            "average_processing_ms": self.average_processing_ms,
            "last_snapshot_completed": self.last_snapshot_completed,
            "subscriber_names": list(self.subscriber_names),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class SubscribersCard:
    """
    Immutable card showing subscriber information.
    """

    count: int
    names: List[str]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Subscribers",
            "count": self.count,
            "names": list(self.names),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class RuntimeHealthCard:
    """
    Immutable card showing runtime health metrics.
    """

    is_running: bool
    total_events: int
    total_errors: int
    average_processing_ms: float
    max_processing_ms: float
    min_processing_ms: float
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Runtime Health",
            "is_running": self.is_running,
            "total_events": self.total_events,
            "total_errors": self.total_errors,
            "average_processing_ms": self.average_processing_ms,
            "max_processing_ms": self.max_processing_ms,
            "min_processing_ms": self.min_processing_ms,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class GuardianActivityCard:
    """
    Immutable card showing Guardian activity summary.
    """

    total_dispatched: int
    event_type_counts: Dict[str, int]
    event_source_counts: Dict[str, int]
    update_count: int
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Guardian Activity",
            "total_dispatched": self.total_dispatched,
            "event_type_counts": dict(self.event_type_counts),
            "event_source_counts": dict(self.event_source_counts),
            "update_count": self.update_count,
            "timestamp": self.timestamp,
        }


class LiveDashboardBridge:
    """
    Bridge between Guardian Live Runtime and Dashboard.

    Provides 6 immutable dashboard cards:
        1. Live Runtime
        2. Recent Events
        3. Dispatch Status
        4. Subscribers
        5. Runtime Health
        6. Guardian Activity

    All cards are frozen dataclasses (immutable DTOs).
    """

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime
        self._refresh_count: int = 0
        self._cached_cards: Dict[str, Any] = {}

    @property
    def card_count(self) -> int:
        """Get the number of dashboard cards."""
        return 6

    @property
    def refresh_count(self) -> int:
        """Get total number of refreshes performed."""
        return self._refresh_count

    def refresh(self) -> None:
        """Refresh all dashboard cards."""
        self._refresh_count += 1
        self._cached_cards = {}

    def get_live_runtime_card(self) -> LiveRuntimeCard:
        """Get Live Runtime status card."""
        status = self._runtime.get_status()
        return LiveRuntimeCard(
            is_running=status["is_running"],
            subscriber_count=status["subscriber_count"],
            total_dispatched=status["total_dispatched"],
            error_count=status["error_count"],
            history_count=status["history_count"],
            timestamp=datetime.now().timestamp(),
        )

    def get_recent_events_card(self) -> RecentEventsCard:
        """Get Recent Events card."""
        stats = self._runtime.history.statistics
        latest = self._runtime.history.latest
        return RecentEventsCard(
            total_events=stats.total_events,
            events_by_type=stats.event_types,
            events_by_source=stats.sources,
            events_by_priority=stats.priorities,
            last_event_type=(
                latest.event.metadata.event_type.name
                if latest else None
            ),
            last_event_source=(
                latest.event.metadata.source.name
                if latest else None
            ),
            timestamp=datetime.now().timestamp(),
        )

    def get_dispatch_status_card(self) -> DispatchStatusCard:
        """Get Dispatch Status card."""
        dispatcher = self._runtime.dispatcher
        stats = self._runtime.history.statistics
        return DispatchStatusCard(
            subscriber_count=dispatcher.subscriber_count,
            total_dispatched=dispatcher.total_dispatched,
            error_count=dispatcher.error_count,
            average_processing_ms=stats.average_processing_ms,
            last_snapshot_completed=(
                self._runtime.last_snapshot.completed
                if self._runtime.last_snapshot
                else False
            ),
            subscriber_names=dispatcher.get_subscriber_names(),
            timestamp=datetime.now().timestamp(),
        )

    def get_subscribers_card(self) -> SubscribersCard:
        """Get Subscribers card."""
        subscribers = self._runtime.dispatcher.subscribers
        return SubscribersCard(
            count=len(subscribers),
            names=[s.get_name() for s in subscribers],
            timestamp=datetime.now().timestamp(),
        )

    def get_runtime_health_card(self) -> RuntimeHealthCard:
        """Get Runtime Health card."""
        stats = self._runtime.history.statistics
        return RuntimeHealthCard(
            is_running=self._runtime.is_running,
            total_events=stats.total_events,
            total_errors=stats.total_errors,
            average_processing_ms=stats.average_processing_ms,
            max_processing_ms=stats.max_processing_ms,
            min_processing_ms=stats.min_processing_ms,
            timestamp=datetime.now().timestamp(),
        )

    def get_guardian_activity_card(self) -> GuardianActivityCard:
        """Get Guardian Activity card."""
        dispatcher = self._runtime.dispatcher
        return GuardianActivityCard(
            total_dispatched=dispatcher.total_dispatched,
            event_type_counts=dispatcher.get_event_counts_by_type(),
            event_source_counts=dispatcher.get_event_counts_by_source(),
            update_count=self._runtime.conversation.update_count,
            timestamp=datetime.now().timestamp(),
        )

    def get_all_cards(self) -> Dict[str, Any]:
        """
        Get all 6 dashboard cards as a dict.

        Returns:
            Dict with all card names as keys and card dicts as values.
        """
        return {
            "live_runtime": self.get_live_runtime_card().to_dict(),
            "recent_events": self.get_recent_events_card().to_dict(),
            "dispatch_status": self.get_dispatch_status_card().to_dict(),
            "subscribers": self.get_subscribers_card().to_dict(),
            "runtime_health": self.get_runtime_health_card().to_dict(),
            "guardian_activity": self.get_guardian_activity_card().to_dict(),
        }
