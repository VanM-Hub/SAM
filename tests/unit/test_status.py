"""
Unit tests for StatusEngine (OP-3).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime, timedelta
import pytest
from sam.experience.pages.home import HomeStatus
from sam.telemetry import TelemetryEvent, TelemetryEventType, EventSeverity, EventCategory, Component
from sam.telemetry.service import TelemetryService
from sam.operations.engine.status import StatusEngine


class TestStatusEngineDefaults:
    def test_initial_status_healthy(self):
        """Empty telemetry returns healthy."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        assert engine.get_status() == HomeStatus.HEALTHY

    def test_initial_health_score_100(self):
        """Empty telemetry returns 100 health score."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        assert engine.get_health_score() == 100.0

    def test_initial_status_message(self):
        """Default status message."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        assert engine.get_status_message() == "Everything is healthy"

    def test_recent_changes_empty(self):
        """No events means no recent changes."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        assert engine.get_recent_changes() == []


class TestStatusEngineHealthScores:
    def test_critical_sets_unhealthy(self):
        """Critical event causes UNHEALTHY status."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.COMPONENT_FAILED,
            component=Component.STORAGE,
            severity=EventSeverity.CRITICAL,
            category=EventCategory.SAFETY,
            message="Storage failed critically",
            timestamp=datetime.utcnow(),
        ))
        assert engine.get_status() == HomeStatus.UNHEALTHY

    def test_unhealthy_score_is_10(self):
        """UNHEALTHY status gives score 10."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.COMPONENT_FAILED,
            component=Component.STORAGE,
            severity=EventSeverity.CRITICAL,
            category=EventCategory.SAFETY,
            message="Failed",
            timestamp=datetime.utcnow(),
        ))
        assert engine.get_health_score() == 10.0

    def test_error_sets_degraded(self):
        """Error event causes DEGRADED status."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.SYSTEM_ERROR,
            component=Component.RUNTIME,
            severity=EventSeverity.ERROR,
            category=EventCategory.SAFETY,
            message="Runtime error",
            timestamp=datetime.utcnow(),
        ))
        assert engine.get_status() == HomeStatus.DEGRADED

    def test_degraded_score_is_40(self):
        """DEGRADED status gives score 40."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.SYSTEM_ERROR,
            component=Component.RUNTIME,
            severity=EventSeverity.ERROR,
            category=EventCategory.SAFETY,
            message="Error",
            timestamp=datetime.utcnow(),
        ))
        assert engine.get_health_score() == 40.0

    def test_recovering_status(self):
        """Recovery events cause RECOVERING status."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_RECOVERING,
            component=Component.RUNTIME,
            severity=EventSeverity.INFO,
            category=EventCategory.RECOVERY,
            message="Recovering",
            timestamp=datetime.utcnow(),
        ))
        assert engine.get_status() == HomeStatus.RECOVERING

    def test_learning_status(self):
        """Many knowledge events cause LEARNING status."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        for i in range(5):
            svc.emit(TelemetryEvent(
                type=TelemetryEventType.KNOWLEDGE_LOADED,
                component=Component.KNOWLEDGE,
                severity=EventSeverity.INFO,
                category=EventCategory.LEARNING,
                message="Learning {}".format(i),
                timestamp=datetime.utcnow(),
            ))
        assert engine.get_status() == HomeStatus.LEARNING

    def test_busy_status(self):
        """Many task events cause BUSY status."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        for i in range(15):
            svc.emit(TelemetryEvent(
                type=TelemetryEventType.TASK_STARTED,
                component=Component.WORKFLOW,
                severity=EventSeverity.INFO,
                category=EventCategory.EXECUTION,
                message="Task {}".format(i),
                timestamp=datetime.utcnow(),
            ))
        assert engine.get_status() == HomeStatus.BUSY

    def test_recent_changes_with_events(self):
        """Recent changes returns formatted dicts."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = StatusEngine(svc)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_COMPLETED,
            component=Component.WORKFLOW,
            severity=EventSeverity.INFO,
            category=EventCategory.EXECUTION,
            message="Task completed",
            timestamp=datetime.utcnow(),
        ))
        changes = engine.get_recent_changes()
        assert len(changes) == 1
        assert changes[0]["severity"] == "info"
        assert "Task completed" in changes[0]["message"]
