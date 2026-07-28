"""TimelineExplorer — Timeline/event explorer for the SAM Console.

Support filtering by mission, severity, date, and keyword search.
No database access — consumes existing event/timeline DTOs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class TimelineEntry:
    """A single timeline event (immutable)."""
    event_id: str
    event_type: str
    title: str
    description: str
    source_id: str = ""
    source_kind: str = "system"
    severity: str = "info"  # critical, error, warning, info, debug
    timestamp: str = ""
    mission_id: str = ""
    duration_ms: float = 0.0
    details: str = ""


@dataclass(frozen=True)
class TimelineExplorer:
    """Timeline explorer view model.

    Filtered and sorted in-memory. No storage access.
    """

    events: Tuple[TimelineEntry, ...] = ()
    total: int = 0
    filtered: int = 0
    current_page: int = 1
    total_pages: int = 1
    page_size: int = 20

    # ── Filtering ───────────────────────────────────────────────────

    def filter_mission(self, mission_id: str) -> TimelineExplorer:
        if not mission_id:
            return self
        filtered = tuple(
            e for e in self.events
            if e.mission_id == mission_id
        )
        return self._rebuild(filtered)

    def filter_severity(self, severity: str) -> TimelineExplorer:
        if not severity or severity == "all":
            return self
        filtered = tuple(
            e for e in self.events if e.severity == severity
        )
        return self._rebuild(filtered)

    def filter_date(self, start: str, end: str) -> TimelineExplorer:
        """Filter events within a date range (ISO format strings)."""
        if not start and not end:
            return self
        filtered = self.events
        if start:
            filtered = tuple(
                e for e in filtered if e.timestamp >= start
            )
        if end:
            filtered = tuple(
                e for e in filtered if e.timestamp <= end
            )
        return self._rebuild(filtered)

    def search(self, keyword: str) -> TimelineExplorer:
        if not keyword:
            return self
        kw = keyword.lower()
        filtered = tuple(
            e for e in self.events
            if kw in e.title.lower()
            or kw in e.description.lower()
            or kw in e.event_id.lower()
            or kw in e.source_id.lower()
        )
        return self._rebuild(filtered)

    def sort_newest_first(self) -> TimelineExplorer:
        sorted_e = tuple(
            sorted(self.events, key=lambda e: e.timestamp, reverse=True)
        )
        return self._rebuild(sorted_e)

    def sort_oldest_first(self) -> TimelineExplorer:
        sorted_e = tuple(
            sorted(self.events, key=lambda e: e.timestamp)
        )
        return self._rebuild(sorted_e)

    def page(self, n: int) -> TimelineExplorer:
        total_pages = max(1, (len(self.events) + self.page_size - 1)
                          // self.page_size)
        n = max(1, min(n, total_pages))
        return TimelineExplorer(
            events=self.events,
            total=self.total,
            filtered=len(self.events),
            current_page=n,
            total_pages=total_pages,
            page_size=self.page_size,
        )

    def next_page(self) -> TimelineExplorer:
        return self.page(self.current_page + 1)

    def prev_page(self) -> TimelineExplorer:
        return self.page(self.current_page - 1)

    def jump_to(self, index: int) -> Optional[TimelineEntry]:
        """Jump to a specific event by index. Returns the event."""
        if 0 <= index < len(self.events):
            return self.events[index]
        return None

    # ── Queries ──────────────────────────────────────────────────────

    @property
    def critical_count(self) -> int:
        return sum(1 for e in self.events if e.severity == "critical")

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.events if e.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.events if e.severity == "warning")

    @property
    def visible_events(self) -> Tuple[TimelineEntry, ...]:
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return self.events[start:end]

    @property
    def summary_line(self) -> str:
        return (
            f"Timeline: {self.total} events, "
            f"{self.critical_count} critical, "
            f"{self.error_count} errors, "
            f"{self.warning_count} warnings"
        )

    # ── Internal ─────────────────────────────────────────────────────

    def _rebuild(self, filtered: Tuple[TimelineEntry, ...]) -> TimelineExplorer:
        total_pages = max(1, (len(filtered) + self.page_size - 1)
                          // self.page_size)
        return TimelineExplorer(
            events=filtered,
            total=self.total,
            filtered=len(filtered),
            current_page=min(self.current_page, total_pages),
            total_pages=total_pages,
            page_size=self.page_size,
        )


# ── Factory ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TimelineExplorerFactory:
    """Creates TimelineExplorer from raw event data."""

    @staticmethod
    def from_event_list(events: list) -> TimelineExplorer:
        """Build from a list of event dicts."""
        entries: list = []
        for ev in events:
            entries.append(TimelineEntry(
                event_id=str(ev.get('event_id', ev.get('id', ''))),
                event_type=str(ev.get('event_type', ev.get('type', ''))),
                title=str(ev.get('title', '')),
                description=str(ev.get('description', '')),
                source_id=str(ev.get('source_id', '')),
                source_kind=str(ev.get('source_kind', 'system')),
                severity=str(ev.get('severity', 'info')),
                timestamp=str(ev.get('timestamp', '')),
                mission_id=str(ev.get('mission_id', '')),
                duration_ms=float(ev.get('duration_ms', 0.0)),
                details=str(ev.get('details', '')),
            ))

        return TimelineExplorer(
            events=tuple(entries),
            total=len(entries),
            filtered=len(entries),
        )

    @staticmethod
    def from_timeline_dto(dto: object) -> TimelineExplorer:
        """Build from a Timeline or event list DTO."""
        if dto is None:
            return TimelineExplorer()

        events = getattr(dto, 'events', getattr(dto, 'items', []))
        if isinstance(events, (tuple, list)):
            return TimelineExplorerFactory.from_event_list(list(events))

        return TimelineExplorer()

    @staticmethod
    def empty() -> TimelineExplorer:
        return TimelineExplorer()
