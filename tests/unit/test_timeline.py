"""
Unit tests for Timeline (OP-4).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime, timedelta
import pytest
from sam.experience.models.timeline import (
    TimelineModel, ActivityItem, ActivityType,
    ActivitySeverity, TimelineFilter,
)
from sam.experience.timeline import TimelineBuilder
from sam.telemetry import (
    TelemetryEvent, TelemetryEventType, EventSeverity,
    EventCategory, Component, TelemetryService,
)


# ============================================================================
# 1. ActivityType & ActivitySeverity Enums
# ============================================================================

class TestActivityEnums:
    def test_activity_types_exist(self):
        """All ActivityType members exist."""
        assert ActivityType.TASK.value == "task"
        assert ActivityType.SYSTEM.value == "system"
        assert ActivityType.KNOWLEDGE.value == "knowledge"

    def test_activity_severities_exist(self):
        """All ActivitySeverity members exist."""
        assert ActivitySeverity.SUCCESS.value == "success"
        assert ActivitySeverity.ERROR.value == "error"

    def test_all_types(self):
        """There are 8 activity types."""
        assert len(list(ActivityType)) == 8

    def test_all_severities(self):
        """There are 5 activity severities."""
        assert len(list(ActivitySeverity)) == 5


# ============================================================================
# 2. ActivityItem
# ============================================================================

class TestActivityItem:
    def test_minimal_item(self):
        """Can create ActivityItem with minimum fields."""
        now = datetime.utcnow()
        item = ActivityItem(
            id="abc123",
            type=ActivityType.TASK,
            severity=ActivitySeverity.INFO,
            title="Task started",
            timestamp=now,
        )
        assert item.id == "abc123"
        assert item.description is None
        assert item.metadata == {}

    def test_full_item(self):
        """Can create ActivityItem with all fields."""
        now = datetime.utcnow()
        item = ActivityItem(
            id="xyz789",
            type=ActivityType.GUARDIAN,
            severity=ActivitySeverity.CRITICAL,
            title="Alert triggered",
            description="Memory usage high",
            timestamp=now,
            duration_ms=500.0,
            correlation_id="corr-001",
            metadata={"alert_id": "a-1"},
        )
        assert item.type == ActivityType.GUARDIAN
        assert item.duration_ms == 500.0
        assert item.metadata["alert_id"] == "a-1"


# ============================================================================
# 3. TimelineFilter
# ============================================================================

class TestTimelineFilter:
    def test_default_filter(self):
        """Default filter has empty lists and no query."""
        f = TimelineFilter()
        assert f.types == []
        assert f.severities == []
        assert f.query is None
        assert f.limit == 100

    def test_custom_filter(self):
        """Can create TimelineFilter with custom values."""
        now = datetime.utcnow()
        f = TimelineFilter(
            types=[ActivityType.TASK],
            severities=[ActivitySeverity.ERROR],
            query="test",
            from_time=now,
            limit=50,
        )
        assert len(f.types) == 1
        assert f.query == "test"
        assert f.limit == 50


# ============================================================================
# 4. TimelineModel
# ============================================================================

class TestTimelineModel:
    def test_minimal_model(self):
        """Can create TimelineModel."""
        now = datetime.utcnow()
        f = TimelineFilter()
        model = TimelineModel(
            activities=[],
            total=0,
            filtered=0,
            filters=f,
        )
        assert model.total == 0
        assert model.filtered == 0
        assert model.filters == f

    def test_model_with_items(self):
        """TimelineModel with activities."""
        now = datetime.utcnow()
        items = [
            ActivityItem(id="1", type=ActivityType.TASK, severity=ActivitySeverity.INFO, title="T1", timestamp=now),
            ActivityItem(id="2", type=ActivityType.SYSTEM, severity=ActivitySeverity.SUCCESS, title="T2", timestamp=now),
        ]
        model = TimelineModel(
            activities=items,
            total=10,
            filtered=2,
            filters=TimelineFilter(limit=2),
        )
        assert len(model.activities) == 2
        assert model.total == 10
        assert model.filtered == 2

    def test_model_is_frozen(self):
        """TimelineModel is immutable."""
        now = datetime.utcnow()
        model = TimelineModel(
            activities=[],
            total=0,
            filtered=0,
            filters=TimelineFilter(),
        )
        with pytest.raises((TypeError, Exception)):
            model.total = 5


# ============================================================================
# 5. TimelineBuilder
# ============================================================================

class TestTimelineBuilder:
    def test_build_with_empty_telemetry(self):
        """Building with empty telemetry returns empty timeline."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        builder = TimelineBuilder(svc)
        model = builder.build()
        assert len(model.activities) == 0
        assert model.total == 0

    def test_single_event_becomes_activity(self):
        """Single event becomes one activity item."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="SAM runtime started",
        ))
        builder = TimelineBuilder(svc)
        model = builder.build()
        assert len(model.activities) == 1
        assert model.activities[0].type == ActivityType.SYSTEM
        assert model.activities[0].severity == ActivitySeverity.INFO

    def test_multiple_events_with_same_correlation_id_merged(self):
        """Events with same correlation_id are merged."""
        now = datetime.utcnow()
        corr = "workflow-001"
        svc = TelemetryService(max_events=100, enable_cache=False)

        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_STARTED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Repair task started",
            correlation_id=corr,
            timestamp=now,
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.KNOWLEDGE_SEARCHED,
            component=Component.KNOWLEDGE,
            category=EventCategory.EXECUTION,
            message="Looking for schematics",
            correlation_id=corr,
            timestamp=now + timedelta(seconds=5),
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_COMPLETED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Repair completed",
            correlation_id=corr,
            timestamp=now + timedelta(seconds=10),
        ))

        builder = TimelineBuilder(svc)
        model = builder.build()
        assert len(model.activities) == 1
        assert model.activities[0].metadata.get("events_count", 0) >= 3

    def test_activity_type_mapping_task(self):
        """Task events map to ActivityType.TASK."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_CREATED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Task created",
        ))
        builder = TimelineBuilder(svc)
        model = builder.build()
        assert model.activities[0].type == ActivityType.TASK

    def test_activity_type_mapping_knowledge(self):
        """Knowledge events map to ActivityType.KNOWLEDGE."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.KNOWLEDGE_LOADED,
            component=Component.KNOWLEDGE,
            category=EventCategory.LEARNING,
            message="Knowledge loaded",
        ))
        builder = TimelineBuilder(svc)
        model = builder.build()
        assert model.activities[0].type == ActivityType.KNOWLEDGE

    def test_severity_mapping_error(self):
        """Error events map to ActivitySeverity.ERROR."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.SYSTEM_ERROR,
            component=Component.RUNTIME,
            severity=EventSeverity.ERROR,
            category=EventCategory.SAFETY,
            message="Runtime error",
        ))
        builder = TimelineBuilder(svc)
        model = builder.build()
        assert model.activities[0].severity == ActivitySeverity.ERROR

    def test_severity_mapping_critical(self):
        """Critical events map to ActivitySeverity.CRITICAL."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.COMPONENT_FAILED,
            component=Component.STORAGE,
            severity=EventSeverity.CRITICAL,
            category=EventCategory.SAFETY,
            message="Storage failed",
        ))
        builder = TimelineBuilder(svc)
        model = builder.build()
        assert model.activities[0].severity == ActivitySeverity.CRITICAL

    def test_humanize_runtime_started(self):
        """Runtime started becomes 'SAM started'."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="runtime started",
        ))
        builder = TimelineBuilder(svc)
        model = builder.build()
        assert "SAM started" in model.activities[0].title

    def test_humanize_task_failed(self):
        """Task failed includes message."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_FAILED,
            component=Component.WORKFLOW,
            severity=EventSeverity.ERROR,
            category=EventCategory.EXECUTION,
            message="Connection timeout",
        ))
        builder = TimelineBuilder(svc)
        model = builder.build()
        assert "Task failed" in model.activities[0].title
        assert "Connection timeout" in model.activities[0].description

    def test_filter_by_query(self):
        """Query filter works on activity titles."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="started",
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.KNOWLEDGE_LOADED,
            component=Component.KNOWLEDGE,
            category=EventCategory.LEARNING,
            message="loaded",
        ))
        builder = TimelineBuilder(svc)
        model = builder.build(TimelineFilter(query="SAM"))
        assert len(model.activities) == 1
        assert "SAM" in model.activities[0].title

    def test_get_timeline_helper(self):
        """get_timeline() returns list of activities."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="started",
        ))
        builder = TimelineBuilder(svc)
        activities = builder.get_timeline()
        assert len(activities) == 1

    def test_duration_in_merged_events(self):
        """Merged events calculate duration_ms."""
        now = datetime.utcnow()
        corr = "wf-duration"
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_STARTED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Started",
            correlation_id=corr,
            timestamp=now,
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_COMPLETED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Completed",
            correlation_id=corr,
            timestamp=now + timedelta(seconds=2),
        ))
        builder = TimelineBuilder(svc)
        model = builder.build()
        assert model.activities[0].duration_ms is not None
        assert model.activities[0].duration_ms > 0

    def test_activities_sorted_by_timestamp(self):
        """Activities are sorted descending by timestamp."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        now = datetime.utcnow()
        # Emit backward so sorting is tested
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STOPPED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="Stopped",
            timestamp=now,
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="Started",
            timestamp=now + timedelta(hours=1),
        ))
        builder = TimelineBuilder(svc)
        model = builder.build()
        assert len(model.activities) == 2
        assert model.activities[0].title == "SAM started"
        assert model.activities[1].title == "SAM stopped"
