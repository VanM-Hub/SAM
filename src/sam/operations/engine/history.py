"""
History Engine — membaca telemetry dan menyusun riwayat kronologis.
"""

import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from ...telemetry.service import TelemetryService
from ...experience.models.history import (
    HistoryEntry, HistoryDay, HistoryModel, HistoryFilter,
    HistoryEntryType, HistoryEntrySeverity,
)

logger = structlog.get_logger()


class HistoryEngine:
    """Engine untuk menyusun riwayat dari telemetry."""

    # Mapping event component -> HistoryEntryType
    COMPONENT_TYPE_MAP = {
        "runtime": HistoryEntryType.SYSTEM,
        "guardian": HistoryEntryType.SYSTEM,
        "workflow": HistoryEntryType.TASK,
        "planner": HistoryEntryType.TASK,
        "execution": HistoryEntryType.TASK,
        "knowledge": HistoryEntryType.KNOWLEDGE,
        "memory": HistoryEntryType.KNOWLEDGE,
        "plugin": HistoryEntryType.PLUGIN,
        "mission": HistoryEntryType.SYSTEM,
        "operator": HistoryEntryType.USER,
    }

    def __init__(self, telemetry):
        self.telemetry = telemetry

    def get_history(self, filters=None):
        """Get history from telemetry."""
        if filters is None:
            filters = HistoryFilter()

        # Ambil events dari telemetry
        events = self._get_events(filters)

        # Konversi ke HistoryEntry
        entries = [self._event_to_history(e) for e in events]

        # Filter text
        if filters.query:
            entries = self._filter_by_query(entries, filters.query)

        # Kelompokkan per hari
        days = self._group_by_day(entries)

        total = len(entries)

        return HistoryModel(
            days=days,
            total=total,
            filtered=len(entries),
            filters=filters,
            last_updated=datetime.utcnow()
        )

    def _get_events(self, filters):
        """Ambil events dari telemetry dengan filter waktu."""
        query = {}
        if filters.from_date:
            query["from"] = filters.from_date
        if filters.to_date:
            query["to"] = filters.to_date

        events = self.telemetry.query(query)

        # Filter berdasarkan severity
        if filters.severities:
            severity_values = [s.value for s in filters.severities]
            events = [e for e in events if e.severity.value in severity_values]

        # Filter berdasarkan tipe
        if filters.types:
            type_values = [t.value for t in filters.types]
            events = [e for e in events if self._get_type(e) in type_values]

        # Limit
        if filters.limit and len(events) > filters.limit:
            events = events[:filters.limit]

        return events

    def _get_type(self, event):
        """Tentukan HistoryEntryType dari event."""
        return self.COMPONENT_TYPE_MAP.get(
            event.component.value,
            HistoryEntryType.SYSTEM,
        )

    def _get_severity(self, event):
        """Tentukan HistoryEntrySeverity dari event."""
        severity_map = {
            "info": HistoryEntrySeverity.INFO,
            "success": HistoryEntrySeverity.SUCCESS,
            "warning": HistoryEntrySeverity.WARNING,
            "error": HistoryEntrySeverity.ERROR,
            "critical": HistoryEntrySeverity.CRITICAL,
        }
        return severity_map.get(event.severity.value, HistoryEntrySeverity.INFO)

    def _event_to_history(self, event):
        """Ubah event menjadi HistoryEntry."""
        title = event.message[:100] if event.message else "{}".format(event.type.value)
        desc = event.message if event.message and len(event.message) > 50 else None
        return HistoryEntry(
            id=event.id,
            type=self._get_type(event),
            severity=self._get_severity(event),
            title=title,
            description=desc,
            timestamp=event.timestamp,
            duration_ms=event.duration_ms,
            correlation_id=event.correlation_id,
            user=None,
            metadata=event.metadata,
        )

    def _filter_by_query(self, entries, query):
        """Filter entries by text query."""
        query_lower = query.lower()
        result = []
        for entry in entries:
            if query_lower in entry.title.lower():
                result.append(entry)
            elif entry.description and query_lower in entry.description.lower():
                result.append(entry)
        return result

    def _group_by_day(self, entries):
        """Kelompokkan entries per hari."""
        day_groups = defaultdict(list)
        for entry in entries:
            day_key = entry.timestamp.date()
            day_groups[day_key].append(entry)

        days = []
        for day_date, day_entries in sorted(day_groups.items(), reverse=True):
            # Urutkan entries dalam hari
            day_entries.sort(key=lambda e: e.timestamp, reverse=True)
            from datetime import datetime as dt
            days.append(HistoryDay(
                date=dt.combine(day_date, dt.min.time()),
                entries=day_entries,
                count=len(day_entries),
            ))

        return days

    def get_timeline(self, limit=50):
        """Quick timeline without grouping."""
        filters = HistoryFilter(limit=limit)
        model = self.get_history(filters)
        entries = []
        for day in model.days:
            entries.extend(day.entries)
        return entries[:limit]

    def search(self, query, limit=50):
        """Search history."""
        filters = HistoryFilter(query=query, limit=limit)
        model = self.get_history(filters)
        entries = []
        for day in model.days:
            entries.extend(day.entries)
        return entries[:limit]
