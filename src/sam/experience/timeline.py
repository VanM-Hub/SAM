"""
Timeline Builder — kumpulkan event dari Telemetry, kelompokkan ke dalam aktivitas.
"""

import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..telemetry.service import TelemetryService
from ..telemetry.event import TelemetryEvent
from ..language.mapping import humanize
from .models.timeline import TimelineModel, ActivityItem, ActivityType, ActivitySeverity, TimelineFilter

logger = structlog.get_logger()


class TimelineBuilder:
    """Build human-readable timeline from telemetry events."""

    # Mapping event type → activity type
    EVENT_TO_ACTIVITY = {
        "task": ActivityType.TASK,
        "workflow": ActivityType.TASK,
        "knowledge": ActivityType.KNOWLEDGE,
        "memory": ActivityType.MEMORY,
        "plugin": ActivityType.PLUGIN,
        "mission": ActivityType.MISSION,
        "guardian": ActivityType.GUARDIAN,
        "runtime": ActivityType.SYSTEM,
        "system": ActivityType.SYSTEM,
    }

    # Mapping severity
    SEVERITY_MAP = {
        "trace": ActivitySeverity.INFO,
        "debug": ActivitySeverity.INFO,
        "info": ActivitySeverity.INFO,
        "success": ActivitySeverity.SUCCESS,
        "warning": ActivitySeverity.WARNING,
        "error": ActivitySeverity.ERROR,
        "critical": ActivitySeverity.CRITICAL,
    }

    def __init__(self, telemetry: TelemetryService):
        self.telemetry = telemetry

    def build(self, filters=None):
        """Build timeline from telemetry events."""
        if filters is None:
            filters = TimelineFilter()

        # Ambil events
        events = self._get_events(filters)

        # Kelompokkan menjadi aktivitas
        activities = self._group_events(events)

        # Filter berdasarkan query
        if filters.query:
            activities = self._filter_by_query(activities, filters.query)

        total = len(activities)

        # Limit
        if filters.limit and len(activities) > filters.limit:
            activities = activities[:filters.limit]

        return TimelineModel(
            activities=activities,
            total=total,
            filtered=len(activities),
            filters=filters,
            last_updated=datetime.utcnow()
        )

    def _get_events(self, filters):
        """Ambil events dari telemetry."""
        # Query telemetry
        query_filters = {}
        if filters.from_time:
            query_filters["from"] = filters.from_time
        if filters.to_time:
            query_filters["to"] = filters.to_time

        events = self.telemetry.query(query_filters)

        # Filter berdasarkan severity
        if filters.severities:
            severity_values = [s.value for s in filters.severities]
            events = [e for e in events if e.severity.value in severity_values]

        # Filter berdasarkan tipe
        if filters.types:
            type_values = [t.value for t in filters.types]
            events = [e for e in events if self._get_activity_type(e) in type_values]

        return events

    def _get_activity_type(self, event):
        """Tentukan ActivityType dari event."""
        for key, activity_type in self.EVENT_TO_ACTIVITY.items():
            if key in event.type.value:
                return activity_type
        return ActivityType.SYSTEM

    def _get_activity_severity(self, event):
        """Tentukan ActivitySeverity dari event."""
        return self.SEVERITY_MAP.get(event.severity.value, ActivitySeverity.INFO)

    def _group_events(self, events):
        """Kelompokkan events menjadi aktivitas yang bermakna."""
        # Group berdasarkan correlation_id atau workflow_id
        groups = {}
        for event in events:
            key = event.correlation_id or event.workflow_id or "single_{}".format(event.id)
            if key not in groups:
                groups[key] = []
            groups[key].append(event)

        activities = []
        for group_events in groups.values():
            if len(group_events) == 1:
                # Single event → aktivitas tunggal
                activities.append(self._event_to_activity(group_events[0]))
            else:
                # Multiple events → gabungkan
                activities.append(self._merge_events(group_events))

        # Urutkan berdasarkan timestamp (descending)
        activities.sort(key=lambda a: a.timestamp, reverse=True)
        return activities

    def _event_to_activity(self, event):
        """Ubah satu event menjadi ActivityItem."""
        return ActivityItem(
            id=event.id,
            type=self._get_activity_type(event),
            severity=self._get_activity_severity(event),
            title=self._humanize_event(event),
            description=event.message,
            timestamp=event.timestamp,
            duration_ms=event.duration_ms,
            correlation_id=event.correlation_id,
            metadata=event.metadata,
        )

    def _merge_events(self, events):
        """Gabungkan beberapa event menjadi satu aktivitas."""
        # Ambil event pertama sebagai dasar
        first = events[0]
        last = events[-1]

        # Buat judul dari event pertama
        title = self._humanize_event(first)

        # Durasi dari first ke last
        duration_ms = (last.timestamp - first.timestamp).total_seconds() * 1000

        # Deskripsi: ringkasan dari semua event
        descriptions = [e.message for e in events[:3]]
        description = "; ".join(descriptions)
        if len(events) > 3:
            description += " (and {} more events)".format(len(events) - 3)

        return ActivityItem(
            id=first.id,
            type=self._get_activity_type(first),
            severity=self._get_activity_severity(first),
            title=title,
            description=description,
            timestamp=first.timestamp,
            duration_ms=duration_ms,
            correlation_id=first.correlation_id,
            metadata={"events_count": len(events)},
        )

    def _humanize_event(self, event):
        """Ubah event menjadi kalimat manusia."""
        # Mapping event type → human sentence
        event_map = {
            "task.created": "Task created",
            "task.started": "Task started",
            "task.progress": "Progress",
            "task.completed": "Task completed successfully",
            "task.failed": "Task failed: {message}",
            "task.cancelled": "Task cancelled",
            "knowledge.loaded": "Knowledge loaded",
            "knowledge.updated": "Knowledge updated",
            "knowledge.searched": "Looking for information",
            "knowledge.found": "Information found",
            "knowledge.not_found": "Information not found",
            "memory.retrieved": "Looking at history",
            "memory.stored": "Remembered",
            "memory.cleared": "Memory cleared",
            "plugin.installed": "Plugin installed",
            "plugin.enabled": "Plugin enabled",
            "plugin.disabled": "Plugin disabled",
            "guardian.alert": "\u26a0\ufe0f Alert: {message}",
            "guardian.action": "Guardian action: {message}",
            "recommendation.created": "\U0001f4a1 Recommendation: {message}",
            "runtime.started": "SAM started",
            "runtime.stopped": "SAM stopped",
            "runtime.ready": "SAM ready",
            "component.healthy": "Component healthy",
            "component.degraded": "\u26a0\ufe0f Component degraded: {message}",
            "component.failed": "\u274c Component failed: {message}",
            "component.recovered": "\u2705 Component recovered",
            "operator.action": "Operator action: {message}",
            "system.boot": "System boot",
            "system.shutdown": "System shutdown",
            "system.error": "\u274c System error: {message}",
        }

        # Cari template
        template = "Event"
        for key, tmpl in event_map.items():
            if key in event.type.value:
                template = tmpl
                break

        # Humanize message
        message = humanize(event.message)

        if "{message}" in template:
            return template.format(message=message)

        return template

    def _filter_by_query(self, activities, query):
        """Filter activities by text query."""
        query_lower = query.lower()
        result = []
        for activity in activities:
            if query_lower in activity.title.lower():
                result.append(activity)
            elif activity.description and query_lower in activity.description.lower():
                result.append(activity)
        return result

    def get_timeline(self, limit=50, severity=None):
        """Quick timeline builder."""
        filters = TimelineFilter(limit=limit)
        if severity:
            filters.severities = [ActivitySeverity(severity)]
        model = self.build(filters)
        return model.activities
