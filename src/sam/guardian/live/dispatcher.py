"""
Guardian Event Dispatcher.

Synchronous event dispatcher with priority sorting.
No async, no threading, no network.

Pipeline:
    publish → priority sort → dispatch → collect results → snapshot
"""

import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict

from .event import (
    GuardianEvent,
    GuardianEventType,
    GuardianEventPriority,
    GuardianEventSource,
    GuardianEventSnapshot,
)
from .subscriber import GuardianEventSubscriber


class GuardianEventDispatcher:
    """
    Synchronous event dispatcher for the Guardian Live Runtime.

    Dispatches events to registered subscribers in priority order.
    Produces a snapshot after each dispatch cycle.
    """

    def __init__(self) -> None:
        self._subscribers: List[GuardianEventSubscriber] = []
        self._dispatch_history: List[GuardianEvent] = []
        self._snapshot_history: List[GuardianEventSnapshot] = []
        self._last_snapshot: Optional[GuardianEventSnapshot] = None
        self._error_count: int = 0
        self._total_dispatched: int = 0

    def register(self, subscriber: GuardianEventSubscriber) -> None:
        """Register a subscriber."""
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)

    def unregister(self, subscriber: GuardianEventSubscriber) -> None:
        """Unregister a subscriber."""
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    def dispatch(self, event: GuardianEvent) -> GuardianEventSnapshot:
        """
        Dispatch a single event to all matching subscribers.

        Pipeline:
            1. Find matching subscribers
            2. Sort by priority
            3. Dispatch
            4. Collect results
            5. Create snapshot

        Args:
            event: The event to dispatch.

        Returns:
            A GuardianEventSnapshot for this dispatch cycle.
        """
        start_time = time.time()
        cycle_id = str(uuid.uuid4())
        errors: List[str] = []
        results: List[Dict[str, Any]] = []

        # 1. Find matching subscribers
        matching = [s for s in self._subscribers if s.supports(event)]

        # 2. Sort by subscriber name for deterministic order
        matching.sort(key=lambda s: s.get_name())

        # 3. Dispatch to each matching subscriber
        for subscriber in matching:
            try:
                result = subscriber.handle(event)
                if result is not None:
                    results.append(result)
            except Exception as e:
                err_msg = f"{subscriber.get_name()}: {e}"
                errors.append(err_msg)
                self._error_count += 1

        # 4. Record dispatch
        self._dispatch_history.append(event)
        self._total_dispatched += 1

        # 5. Build priority and source counts
        priority_counts: Dict[str, int] = defaultdict(int)
        source_counts: Dict[str, int] = defaultdict(int)
        priority_counts[event.metadata.priority.name] = 1
        source_counts[event.metadata.source.name] = 1

        # 6. Create snapshot
        elapsed = (time.time() - start_time) * 1000.0
        snapshot = GuardianEventSnapshot(
            cycle_id=cycle_id,
            timestamp=datetime.now().timestamp(),
            total_events=1,
            events=[event],
            priority_counts=dict(priority_counts),
            source_counts=dict(source_counts),
            completed=len(errors) == 0,
            errors=errors,
            duration_ms=elapsed,
        )

        self._snapshot_history.append(snapshot)
        self._last_snapshot = snapshot
        return snapshot

    def dispatch_batch(self, events: List[GuardianEvent]) -> GuardianEventSnapshot:
        """
        Dispatch multiple events in priority order.

        Pipeline:
            1. Sort all events by priority (CRITICAL first)
            2. Dispatch each in order
            3. Collect all results
            4. Create aggregate snapshot

        Args:
            events: List of events to dispatch.

        Returns:
            An aggregate GuardianEventSnapshot for this batch cycle.
        """
        start_time = time.time()
        cycle_id = str(uuid.uuid4())
        errors: List[str] = []
        all_results: List[Dict[str, Any]] = []
        priority_counts: Dict[str, int] = defaultdict(int)
        source_counts: Dict[str, int] = defaultdict(int)

        # 1. Sort by priority (lower value = higher priority)
        sorted_events = sorted(
            events, key=lambda e: e.metadata.priority.value
        )

        # 2. Dispatch each in order
        for event in sorted_events:
            matching = [s for s in self._subscribers if s.supports(event)]
            matching.sort(key=lambda s: s.get_name())

            for subscriber in matching:
                try:
                    result = subscriber.handle(event)
                    if result is not None:
                        all_results.append(result)
                except Exception as e:
                    err_msg = f"{subscriber.get_name()}: {e}"
                    errors.append(err_msg)
                    self._error_count += 1

            self._dispatch_history.append(event)
            self._total_dispatched += 1
            priority_counts[event.metadata.priority.name] += 1
            source_counts[event.metadata.source.name] += 1

        # 3. Create aggregate snapshot
        elapsed = (time.time() - start_time) * 1000.0
        snapshot = GuardianEventSnapshot(
            cycle_id=cycle_id,
            timestamp=datetime.now().timestamp(),
            total_events=len(sorted_events),
            events=sorted_events,
            priority_counts=dict(priority_counts),
            source_counts=dict(source_counts),
            completed=len(errors) == 0,
            errors=errors,
            duration_ms=elapsed,
        )

        self._snapshot_history.append(snapshot)
        self._last_snapshot = snapshot
        return snapshot

    @property
    def subscriber_count(self) -> int:
        """Get the number of registered subscribers."""
        return len(self._subscribers)

    @property
    def total_dispatched(self) -> int:
        """Get total number of events dispatched."""
        return self._total_dispatched

    @property
    def error_count(self) -> int:
        """Get total number of dispatch errors."""
        return self._error_count

    @property
    def last_snapshot(self) -> Optional[GuardianEventSnapshot]:
        """Get the last dispatch snapshot."""
        return self._last_snapshot

    @property
    def subscribers(self) -> List[GuardianEventSubscriber]:
        """Get the list of registered subscribers (read-only)."""
        return list(self._subscribers)

    def get_subscriber_names(self) -> List[str]:
        """Get names of all registered subscribers."""
        return [s.get_name() for s in self._subscribers]

    def clear_history(self) -> None:
        """Clear dispatch and snapshot history."""
        self._dispatch_history.clear()
        self._snapshot_history.clear()
        self._last_snapshot = None

    def get_event_counts_by_type(self) -> Dict[str, int]:
        """Get event counts grouped by type."""
        counts: Dict[str, int] = defaultdict(int)
        for event in self._dispatch_history:
            counts[event.metadata.event_type.name] += 1
        return dict(counts)

    def get_event_counts_by_source(self) -> Dict[str, int]:
        """Get event counts grouped by source."""
        counts: Dict[str, int] = defaultdict(int)
        for event in self._dispatch_history:
            counts[event.metadata.source.name] += 1
        return dict(counts)
