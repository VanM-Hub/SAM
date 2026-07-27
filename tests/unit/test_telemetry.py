"""
Unit tests for SAM Telemetry Foundation (OP-1).
"""

import sys
import os
import json
from datetime import datetime, timedelta
from uuid import uuid4

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from sam.telemetry import (
    TelemetryEvent,
    EventSeverity,
    EventCategory,
    TelemetryEventType,
    Component,
    TelemetryService,
    RingBuffer,
    Filter,
    TelemetryStorage,
    load_event_schema,
    validate_against_schema,
)
from sam.language import humanize, humanize_event_message, HumanActivityCategory


# ============================================================================
# 1. Component Enum
# ============================================================================

class TestComponent:
    def test_all_components_have_valid_values(self):
        """Every Component enum member has a non-empty string value."""
        for comp in Component:
            assert len(comp.value) > 0

    def test_telemetry_component_exists(self):
        """TELEMETRY is a registered component."""
        assert Component.TELEMETRY.value == "telemetry"

    def test_list_all_returns_strings(self):
        """list_all() returns string values, not enum members."""
        all_comps = Component.list_all()
        assert isinstance(all_comps, list)
        assert len(all_comps) >= 18
        assert "runtime" in all_comps
        assert "telemetry" in all_comps


# ============================================================================
# 2. EventType Enum
# ============================================================================

class TestTelemetryEventType:
    def test_runtime_events_exist(self):
        """Runtime lifecycle events are present."""
        assert TelemetryEventType.RUNTIME_STARTED.value == "runtime.started"
        assert TelemetryEventType.RUNTIME_STOPPED.value == "runtime.stopped"
        assert TelemetryEventType.RUNTIME_CRASHED.value == "runtime.crashed"

    def test_task_events_exist(self):
        """Task/workflow events are present."""
        assert TelemetryEventType.TASK_CREATED.value == "task.created"
        assert TelemetryEventType.TASK_COMPLETED.value == "task.completed"
        assert TelemetryEventType.TASK_FAILED.value == "task.failed"

    def test_list_all_returns_strings(self):
        """list_all() returns string values."""
        types = TelemetryEventType.list_all()
        assert isinstance(types, list)
        assert len(types) >= 30
        assert "runtime.started" in types

    def test_is_valid(self):
        """is_valid() correctly validates event types."""
        assert TelemetryEventType.is_valid("runtime.started") is True
        assert TelemetryEventType.is_valid("invalid.event") is False


# ============================================================================
# 3. TelemetryEvent Model
# ============================================================================

class TestTelemetryEvent:
    def test_create_minimal_event(self):
        """Can create an event with minimum required fields."""
        event = TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="SAM runtime started",
        )
        assert event.id is not None
        assert len(event.id) == 8
        assert event.severity == EventSeverity.INFO
        assert event.metadata == {}

    def test_create_full_event(self):
        """Can create an event with all fields."""
        now = datetime.utcnow()
        event = TelemetryEvent(
            type=TelemetryEventType.TASK_FAILED,
            component=Component.EXECUTION,
            severity=EventSeverity.ERROR,
            category=EventCategory.EXECUTION,
            message="Task failed",
            metadata={"task_id": "t-001", "reason": "timeout"},
            correlation_id="corr-123",
            session_id="sess-456",
            workflow_id="wf-789",
            timestamp=now,
            duration_ms=1500.5,
        )
        assert event.type == TelemetryEventType.TASK_FAILED
        assert event.metadata["task_id"] == "t-001"
        assert event.duration_ms == 1500.5

    def test_event_is_frozen(self):
        """TelemetryEvent is immutable via frozen=True."""
        from pydantic_core._pydantic_core import ValidationError as PydanticValidationError
        event = TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="Started",
        )
        with pytest.raises((TypeError, PydanticValidationError)):
            event.message = "changed"

    def test_to_json(self):
        """to_json() produces valid JSON."""
        event = TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="Started",
        )
        data = json.loads(event.to_json())
        assert data["type"] == "runtime.started"
        assert data["component"] == "runtime"
        assert "id" in data

    def test_to_human(self):
        """to_human() returns human-friendly string."""
        event = TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="SAM started",
        )
        human = event.to_human()
        assert human.startswith("[")
        assert "INFO" in human or "info" in human
        assert "SAM started" in human

    def test_message_max_length(self):
        """Message cannot exceed 500 characters."""
        with pytest.raises(Exception):
            TelemetryEvent(
                type=TelemetryEventType.RUNTIME_STARTED,
                component=Component.RUNTIME,
                category=EventCategory.LIFECYCLE,
                message="x" * 501,
            )

    def test_metadata_defaults_to_dict(self):
        """Default metadata is an empty dict."""
        event = TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="Started",
        )
        assert event.metadata == {}


# ============================================================================
# 4. Ring Buffer
# ============================================================================

class TestRingBuffer:
    def test_push_and_get_recent(self):
        """Events can be pushed and retrieved."""
        buf = RingBuffer(max_size=10)
        for i in range(5):
            buf.push(self._make_event("test.{}".format(i)))
        assert len(buf) == 5
        recent = buf.get_recent(3)
        assert len(recent) == 3

    def test_max_size_respected(self):
        """Ring buffer does not exceed max_size."""
        buf = RingBuffer(max_size=5)
        for i in range(10):
            buf.push(self._make_event("test.{}".format(i)))
        assert len(buf) == 5

    def test_get_all_returns_all(self):
        """get_all() returns all events currently in buffer."""
        buf = RingBuffer(max_size=100)
        for i in range(20):
            buf.push(self._make_event("test.{}".format(i)))
        all_events = buf.get_all()
        assert len(all_events) == 20

    def test_get_latest(self):
        """get_latest() returns the most recent event."""
        buf = RingBuffer(max_size=10)
        buf.push(self._make_event("first"))
        buf.push(self._make_event("second"))
        latest = buf.get_latest()
        assert latest is not None
        assert latest.type == self._make_event("second").type

    def test_get_latest_empty(self):
        """get_latest() returns None on empty buffer."""
        buf = RingBuffer()
        assert buf.get_latest() is None

    def test_clear(self):
        """clear() empties the buffer."""
        buf = RingBuffer(max_size=10)
        for i in range(5):
            buf.push(self._make_event("test.{}".format(i)))
        assert len(buf) == 5
        buf.clear()
        assert len(buf) == 0

    @staticmethod
    def _make_event(suffix):
        return TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="Event {}".format(suffix),
        )


# ============================================================================
# 5. Filter
# ============================================================================

class TestFilter:
    def test_filter_by_severity(self):
        """Filter works on severity level."""
        events = [
            self._event(sev=EventSeverity.INFO),
            self._event(sev=EventSeverity.ERROR),
            self._event(sev=EventSeverity.WARNING),
        ]
        result = Filter.apply(events, {"severity": "error"})
        assert len(result) == 1
        assert result[0].severity == EventSeverity.ERROR

    def test_filter_by_component(self):
        """Filter works on component."""
        events = [
            self._event(comp=Component.RUNTIME),
            self._event(comp=Component.GUARDIAN),
            self._event(comp=Component.RUNTIME),
        ]
        result = Filter.apply(events, {"component": "runtime"})
        assert len(result) == 2

    def test_filter_by_category(self):
        """Filter works on category."""
        events = [
            self._event(cat=EventCategory.LIFECYCLE),
            self._event(cat=EventCategory.EXECUTION),
        ]
        result = Filter.apply(events, {"category": "execution"})
        assert len(result) == 1

    def test_filter_by_time_range(self):
        """Filter works on time range."""
        now = datetime.utcnow()
        past = now - timedelta(hours=2)
        future = now + timedelta(hours=2)

        event_past = self._event(ts=past)
        event_now = self._event(ts=now)
        event_future = self._event(ts=future)

        events = [event_past, event_now, event_future]
        result = Filter.apply(events, {"from": now - timedelta(hours=1)})
        assert len(result) == 2  # now and future

    def test_multiple_filters(self):
        """Multiple filters apply together."""
        events = [
            self._event(sev=EventSeverity.INFO, comp=Component.RUNTIME, cat=EventCategory.LIFECYCLE),
            self._event(sev=EventSeverity.ERROR, comp=Component.RUNTIME, cat=EventCategory.EXECUTION),
            self._event(sev=EventSeverity.ERROR, comp=Component.GUARDIAN, cat=EventCategory.SAFETY),
        ]
        result = Filter.apply(events, {"severity": "error", "component": "runtime"})
        assert len(result) == 1
        assert result[0].severity == EventSeverity.ERROR
        assert result[0].component == Component.RUNTIME

    def test_no_filters_returns_all(self):
        """No filters returns original list."""
        events = [self._event()]
        result = Filter.apply(events, {})
        assert len(result) == 1

    @staticmethod
    def _event(sev=None, comp=None, cat=None, ts=None):
        return TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=comp or Component.RUNTIME,
            severity=sev or EventSeverity.INFO,
            category=cat or EventCategory.LIFECYCLE,
            message="Test event",
            timestamp=ts or datetime.utcnow(),
        )


# ============================================================================
# 6. TelemetryService
# ============================================================================

class TestTelemetryService:
    def test_emit_and_query(self):
        """Service emits events and queries buffer."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        event = self._event()
        svc.emit(event)
        results = svc.query()
        assert len(results) == 1
        assert results[0].id == event.id

    def test_emit_subscribe_notify(self):
        """Subscriber callback is notified on emit."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        received = []

        def callback(event):
            received.append(event)

        svc.subscribe(callback)
        svc.emit(self._event())
        assert len(received) == 1

    def test_unsubscribe(self):
        """Unsubscribed callbacks are not notified."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        received = []

        def callback(event):
            received.append(event)

        svc.subscribe(callback)
        svc.emit(self._event())
        svc.unsubscribe(callback)
        svc.emit(self._event())
        assert len(received) == 1  # only first

    def test_get_recent(self):
        """get_recent returns most recent events."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        for i in range(10):
            svc.emit(self._event())
        recent = svc.get_recent(3)
        assert len(recent) == 3

    def test_get_stats(self):
        """get_stats returns correct statistics."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(self._event())
        stats = svc.get_stats()
        assert stats["total_events"] == 1
        assert stats["max_events"] == 100
        assert stats["subscribers"] == 0
        assert stats["cache_enabled"] is False

    def test_close(self):
        """After close, emit is a no-op."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.close()
        svc.emit(self._event())
        assert len(svc.query()) == 0

    @staticmethod
    def _event():
        return TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="Test event",
        )


# ============================================================================
# 7. Storage (SQLite)
# ============================================================================

class TestTelemetryStorage:
    def test_save_and_query(self, tmp_path):
        """Events are saved and can be queried back."""
        db_path = str(tmp_path / "test_cache.db")
        storage = TelemetryStorage(db_path)
        event = self._event()
        storage.save(event)
        results = storage.query()
        assert len(results) == 1
        assert results[0].id == event.id
        assert results[0].type == event.type

    def test_count(self, tmp_path):
        """count() returns correct number."""
        db_path = str(tmp_path / "test_count.db")
        storage = TelemetryStorage(db_path)
        assert storage.count() == 0
        storage.save(self._event())
        assert storage.count() == 1

    @staticmethod
    def _event():
        return TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="Test event",
        )


# ============================================================================
# 8. JSON Schema Validation
# ============================================================================

class TestEventSchema:
    def test_schema_loads(self):
        """event_schema.json loads without error."""
        schema = load_event_schema()
        assert schema["title"] == "TelemetryEvent"
        assert "required" in schema

    def test_valid_event_passes_validation(self):
        """Valid event dict passes validation."""
        event_dict = {
            "id": "abc12345",
            "type": "runtime.started",
            "component": "runtime",
            "severity": "info",
            "category": "lifecycle",
            "message": "Test event",
            "timestamp": datetime.utcnow().isoformat(),
        }
        assert validate_against_schema(event_dict) is True

    def test_invalid_type_fails_validation(self):
        """Invalid event type fails validation."""
        event_dict = {
            "id": "abc12345",
            "type": "invalid.type",
            "component": "runtime",
            "severity": "info",
            "category": "lifecycle",
            "message": "Test",
            "timestamp": datetime.utcnow().isoformat(),
        }
        assert validate_against_schema(event_dict) is False

    def test_missing_required_fails(self):
        """Missing required field fails validation."""
        event_dict = {
            "id": "abc12345",
            "type": "runtime.started",
            # missing component
            "severity": "info",
            "category": "lifecycle",
            "message": "Test",
            "timestamp": datetime.utcnow().isoformat(),
        }
        assert validate_against_schema(event_dict) is False


# ============================================================================
# 9. Human Language Mapping
# ============================================================================

class TestHumanLanguage:
    def test_humanize_known_term(self):
        """Known internal terms are mapped correctly."""
        assert humanize("runtime") == "SAM"
        assert humanize("guardian") == "protection"

    def test_humanize_unknown_term(self):
        """Unknown terms pass through unchanged."""
        assert humanize("unknown_term") == "unknown_term"

    def test_humanize_event_message(self):
        """Event messages get humanized."""
        msg = humanize_event_message("runtime started successfully")
        assert "SAM" in msg

    def test_human_activity_category_enum(self):
        """HumanActivityCategory has expected members."""
        assert HumanActivityCategory.MONITORING.value == "monitoring"
        assert HumanActivityCategory.APPROVAL.value == "approval"
        categories = HumanActivityCategory.list_all()
        assert len(categories) >= 15


# ============================================================================
# 10. Integration: End-to-End
# ============================================================================

class TestIntegration:
    def test_emit_store_query_flow(self, tmp_path):
        """End-to-end: emit, store, query cycle."""
        db_path = str(tmp_path / "e2e.db")
        svc = TelemetryService(max_events=100, enable_cache=True)

        # Override storage path
        svc._storage = TelemetryStorage(db_path)

        # Emit events
        for i in range(5):
            svc.emit(TelemetryEvent(
                type=TelemetryEventType.RUNTIME_STARTED,
                component=Component.RUNTIME,
                category=EventCategory.LIFECYCLE,
                message="Event #{}".format(i),
            ))

        # Query from buffer
        buffer_events = svc.query()
        assert len(buffer_events) == 5

        # Query from storage
        storage_events = svc._storage.query()
        assert len(storage_events) == 5

    def test_emit_with_filter(self):
        """Emit and filter by severity."""
        svc = TelemetryService(max_events=100, enable_cache=False)

        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            severity=EventSeverity.INFO,
            category=EventCategory.LIFECYCLE,
            message="Info event",
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.COMPONENT_FAILED,
            component=Component.STORAGE,
            severity=EventSeverity.CRITICAL,
            category=EventCategory.SAFETY,
            message="Critical event",
        ))

        critical = svc.query({"severity": "critical"})
        assert len(critical) == 1
        assert critical[0].severity == EventSeverity.CRITICAL
