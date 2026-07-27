"""
Unit tests for History Engine (OP-7).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime, timedelta
import pytest
from sam.experience.models.history import (
    HistoryEntry, HistoryDay, HistoryModel, HistoryFilter,
    HistoryEntryType, HistoryEntrySeverity,
)
from sam.operations.engine.history import HistoryEngine
from sam.telemetry import (
    TelemetryEvent, TelemetryEventType, EventSeverity,
    EventCategory, Component, TelemetryService,
)


# ============================================================================
# 1. Enums
# ============================================================================

class TestHistoryEntryType:
    def test_all_types_exist(self):
        assert HistoryEntryType.TASK.value == "task"
        assert HistoryEntryType.SYSTEM.value == "system"
        assert HistoryEntryType.INCIDENT.value == "incident"

    def test_nine_types(self):
        assert len(list(HistoryEntryType)) == 9


class TestHistoryEntrySeverity:
    def test_all_severities_exist(self):
        assert HistoryEntrySeverity.SUCCESS.value == "success"
        assert HistoryEntrySeverity.ERROR.value == "error"

    def test_five_severities(self):
        assert len(list(HistoryEntrySeverity)) == 5


# ============================================================================
# 2. HistoryEntry
# ============================================================================

class TestHistoryEntry:
    def test_minimal_entry(self):
        now = datetime.utcnow()
        e = HistoryEntry(
            id="h1", type=HistoryEntryType.SYSTEM,
            severity=HistoryEntrySeverity.INFO,
            title="System started", timestamp=now,
        )
        assert e.id == "h1"
        assert e.description is None

    def test_full_entry(self):
        now = datetime.utcnow()
        e = HistoryEntry(
            id="h2", type=HistoryEntryType.TASK,
            severity=HistoryEntrySeverity.ERROR,
            title="Task failed", description="Out of memory",
            timestamp=now, duration_ms=5000.0,
            correlation_id="corr-1", user="Van",
        )
        assert e.duration_ms == 5000.0
        assert e.user == "Van"


# ============================================================================
# 3. HistoryDay & HistoryFilter
# ============================================================================

class TestHistoryDay:
    def test_day(self):
        now = datetime.utcnow()
        e = HistoryEntry(id="h1", type=HistoryEntryType.SYSTEM,
                         severity=HistoryEntrySeverity.INFO,
                         title="X", timestamp=now)
        day = HistoryDay(date=now, entries=[e], count=1)
        assert day.count == 1


class TestHistoryFilter:
    def test_default_filter(self):
        f = HistoryFilter()
        assert f.limit == 1000
        assert f.types == []

    def test_custom_filter(self):
        now = datetime.utcnow()
        f = HistoryFilter(
            types=[HistoryEntryType.TASK],
            severities=[HistoryEntrySeverity.ERROR],
            query="fail", from_date=now, limit=50,
        )
        assert f.limit == 50
        assert f.query == "fail"


# ============================================================================
# 4. HistoryModel
# ============================================================================

class TestHistoryModel:
    def test_minimal_model(self):
        model = HistoryModel(days=[], total=0, filtered=0,
                             filters=HistoryFilter())
        assert model.total == 0

    def test_model_is_frozen(self):
        model = HistoryModel(days=[], total=0, filtered=0,
                             filters=HistoryFilter())
        with pytest.raises((TypeError, Exception)):
            model.total = 5


# ============================================================================
# 5. HistoryEngine
# ============================================================================

class TestHistoryEngine:
    def test_empty_telemetry(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = HistoryEngine(svc)
        model = engine.get_history()
        assert model.total == 0
        assert model.days == []

    def test_single_event_becomes_entry(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="SAM started",
        ))
        engine = HistoryEngine(svc)
        model = engine.get_history()
        assert model.total == 1
        assert len(model.days) == 1

    def test_group_by_day(self):
        """Events on different days go to different groups."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="Today", timestamp=now,
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="Yesterday", timestamp=yesterday,
        ))
        engine = HistoryEngine(svc)
        model = engine.get_history()
        assert len(model.days) == 2

    def test_type_mapping_runtime_to_system(self):
        """Runtime events map to HistoryEntryType.SYSTEM."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="started",
        ))
        engine = HistoryEngine(svc)
        model = engine.get_history()
        assert model.days[0].entries[0].type == HistoryEntryType.SYSTEM

    def test_type_mapping_workflow_to_task(self):
        """Workflow events map to HistoryEntryType.TASK."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_STARTED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Task",
        ))
        engine = HistoryEngine(svc)
        model = engine.get_history()
        assert model.days[0].entries[0].type == HistoryEntryType.TASK

    def test_severity_mapping_error(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.SYSTEM_ERROR,
            component=Component.RUNTIME,
            severity=EventSeverity.ERROR,
            category=EventCategory.SAFETY,
            message="Error",
        ))
        engine = HistoryEngine(svc)
        model = engine.get_history()
        assert model.days[0].entries[0].severity == HistoryEntrySeverity.ERROR

    def test_severity_mapping_critical(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.COMPONENT_FAILED,
            component=Component.STORAGE,
            severity=EventSeverity.CRITICAL,
            category=EventCategory.SAFETY,
            message="Critical",
        ))
        engine = HistoryEngine(svc)
        model = engine.get_history()
        assert model.days[0].entries[0].severity == HistoryEntrySeverity.CRITICAL

    def test_filter_by_severity(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            severity=EventSeverity.INFO,
            category=EventCategory.LIFECYCLE,
            message="Info",
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.SYSTEM_ERROR,
            component=Component.RUNTIME,
            severity=EventSeverity.ERROR,
            category=EventCategory.SAFETY,
            message="Error",
        ))
        engine = HistoryEngine(svc)
        filters = HistoryFilter(severities=[HistoryEntrySeverity.ERROR])
        model = engine.get_history(filters)
        assert model.total == 1

    def test_query_filter(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="SAM started",
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.KNOWLEDGE_LOADED,
            component=Component.KNOWLEDGE,
            category=EventCategory.LEARNING,
            message="Knowledge loaded",
        ))
        engine = HistoryEngine(svc)
        filters = HistoryFilter(query="SAM")
        model = engine.get_history(filters)
        assert model.total == 1

    def test_get_timeline(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="started",
        ))
        engine = HistoryEngine(svc)
        entries = engine.get_timeline()
        assert len(entries) == 1

    def test_search(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="SAM started",
        ))
        engine = HistoryEngine(svc)
        results = engine.search("SAM")
        assert len(results) == 1
        assert engine.search("nonexistent") == []
