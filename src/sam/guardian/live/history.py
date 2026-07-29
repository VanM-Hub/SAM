"""
Guardian Event History.

Ring buffer for event history tracking.
Synchronous only. No async, no threading, no network.
"""

from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import math

from .event import (
    GuardianEvent,
    GuardianEventType,
    GuardianEventPriority,
    GuardianEventSource,
)


@dataclass(frozen=True)
class EventRecord:
    """
    Immutable record of a dispatched event with timing info.
    """

    event: GuardianEvent
    dispatched_at: float
    processing_ms: float
    subscriber_count: int
    error_count: int


class HistoryStatistics:
    """
    Computed statistics from event history.
    Immutable after creation.
    """

    def __init__(self, records: List[EventRecord]) -> None:
        self._records = records

    @property
    def total_events(self) -> int:
        return len(self._records)

    @property
    def event_types(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for r in self._records:
            counts[r.event.metadata.event_type.name] += 1
        return dict(counts)

    @property
    def sources(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for r in self._records:
            counts[r.event.metadata.source.name] += 1
        return dict(counts)

    @property
    def priorities(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for r in self._records:
            counts[r.event.metadata.priority.name] += 1
        return dict(counts)

    @property
    def average_processing_ms(self) -> float:
        if not self._records:
            return 0.0
        total = sum(r.processing_ms for r in self._records)
        return round(total / len(self._records), 4)

    @property
    def max_processing_ms(self) -> float:
        if not self._records:
            return 0.0
        return max(r.processing_ms for r in self._records)

    @property
    def min_processing_ms(self) -> float:
        if not self._records:
            return 0.0
        return min(r.processing_ms for r in self._records)

    @property
    def total_errors(self) -> int:
        return sum(r.error_count for r in self._records)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_events": self.total_events,
            "event_types": self.event_types,
            "sources": self.sources,
            "priorities": self.priorities,
            "average_processing_ms": self.average_processing_ms,
            "max_processing_ms": self.max_processing_ms,
            "min_processing_ms": self.min_processing_ms,
            "total_errors": self.total_errors,
        }


class EventHistory:
    """
    Ring buffer for event history.

    Stores EventRecords in a fixed-size buffer. Oldest records
    are dropped when the buffer is full.

    All operations are synchronous and deterministic.
    """

    def __init__(self, max_size: int = 1000) -> None:
        self._max_size = max_size
        self._buffer: List[Optional[EventRecord]] = [None] * max_size
        self._head: int = 0
        self._count: int = 0

    def record(
        self,
        event: GuardianEvent,
        processing_ms: float,
        subscriber_count: int,
        error_count: int,
    ) -> None:
        """
        Record an event dispatch.

        Args:
            event: The dispatched event.
            processing_ms: Processing time in milliseconds.
            subscriber_count: Number of subscribers that handled it.
            error_count: Number of errors during dispatch.
        """
        record = EventRecord(
            event=event,
            dispatched_at=datetime.now().timestamp(),
            processing_ms=processing_ms,
            subscriber_count=subscriber_count,
            error_count=error_count,
        )
        self._buffer[self._head] = record
        self._head = (self._head + 1) % self._max_size
        if self._count < self._max_size:
            self._count += 1

    @property
    def latest(self) -> Optional[EventRecord]:
        """Get the most recent record."""
        if self._count == 0:
            return None
        idx = (self._head - 1) % self._max_size
        return self._buffer[idx]

    @property
    def count(self) -> int:
        """Get total number of records."""
        return self._count

    @property
    def max_size(self) -> int:
        """Get the maximum buffer size."""
        return self._max_size

    def get_all(self) -> List[EventRecord]:
        """
        Get all records in order (oldest first).

        Returns:
            List of EventRecord in chronological order.
        """
        if self._count == 0:
            return []
        if self._count < self._max_size:
            records = self._buffer[:self._count]
        else:
            records = (
                self._buffer[self._head:] + self._buffer[:self._head]
            )
        return [r for r in records if r is not None]

    def filter(
        self,
        event_type: Optional[GuardianEventType] = None,
        source: Optional[GuardianEventSource] = None,
        priority: Optional[GuardianEventPriority] = None,
        min_processing_ms: Optional[float] = None,
        max_processing_ms: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[EventRecord]:
        """
        Filter records by criteria.

        Args:
            event_type: Filter by event type.
            source: Filter by source.
            priority: Filter by priority.
            min_processing_ms: Filter by minimum processing time.
            max_processing_ms: Filter by maximum processing time.
            limit: Maximum number of records to return.

        Returns:
            Filtered list of EventRecords.
        """
        all_records = self.get_all()

        if event_type is not None:
            all_records = [
                r for r in all_records
                if r.event.metadata.event_type == event_type
            ]
        if source is not None:
            all_records = [
                r for r in all_records
                if r.event.metadata.source == source
            ]
        if priority is not None:
            all_records = [
                r for r in all_records
                if r.event.metadata.priority == priority
            ]
        if min_processing_ms is not None:
            all_records = [
                r for r in all_records
                if r.processing_ms >= min_processing_ms
            ]
        if max_processing_ms is not None:
            all_records = [
                r for r in all_records
                if r.processing_ms <= max_processing_ms
            ]

        if limit is not None and limit > 0:
            all_records = all_records[-limit:]

        return all_records

    def snapshot(self) -> 'EventHistory':
        """
        Create a frozen snapshot of the current state.

        Returns:
            A new EventHistory with the same records.
        """
        snap = EventHistory(max_size=self._max_size)
        for r in self.get_all():
            snap.record(
                r.event,
                r.processing_ms,
                r.subscriber_count,
                r.error_count,
            )
        return snap

    @property
    def statistics(self) -> HistoryStatistics:
        """
        Get computed statistics from current records.

        Returns:
            HistoryStatistics object.
        """
        return HistoryStatistics(self.get_all())

    def clear(self) -> None:
        """Clear all records."""
        self._buffer = [None] * self._max_size
        self._head = 0
        self._count = 0

    def is_full(self) -> bool:
        """Check if the buffer is full."""
        return self._count == self._max_size
