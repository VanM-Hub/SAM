"""
Unit tests for Explainability Engine (OP-9).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime, timedelta
import pytest
from sam.experience.models.explain import (
    Explanation, Evidence, Impact, Recommendation, ExplanationSeverity,
)
from sam.operations.engine.explain import ExplainabilityEngine
from sam.operations.engine.templates import ExplanationTemplates
from sam.telemetry import (
    TelemetryEvent, TelemetryEventType, EventSeverity,
    EventCategory, Component, TelemetryService,
)


# ============================================================================
# 1. Enums
# ============================================================================

class TestExplanationSeverity:
    def test_all_severities(self):
        assert ExplanationSeverity.INFO.value == "info"
        assert ExplanationSeverity.ERROR.value == "error"

    def test_four_severities(self):
        assert len(list(ExplanationSeverity)) == 4


# ============================================================================
# 2. Evidence, Impact, Recommendation
# ============================================================================

class TestEvidence:
    def test_minimal_evidence(self):
        now = datetime.utcnow()
        e = Evidence(source="e1", description="Evidence 1", timestamp=now)
        assert e.confidence == 0.8


class TestImpact:
    def test_minimal_impact(self):
        impact = Impact(
            description="System degraded",
            severity=ExplanationSeverity.WARNING,
        )
        assert impact.affected_components == []


class TestRecommendation:
    def test_minimal_rec(self):
        rec = Recommendation(description="Restart service")
        assert rec.priority == 0


# ============================================================================
# 3. Explanation Model
# ============================================================================

class TestExplanation:
    def test_minimal_explanation(self):
        now = datetime.utcnow()
        expl = Explanation(
            id="x1", title="Test", description="Desc",
            severity=ExplanationSeverity.INFO,
            timestamp=now, why="Because",
        )
        assert expl.id == "x1"
        assert expl.confidence == 0.9

    def test_explanation_is_frozen(self):
        now = datetime.utcnow()
        expl = Explanation(
            id="x1", title="Test", description="Desc",
            severity=ExplanationSeverity.INFO,
            timestamp=now, why="Because",
        )
        with pytest.raises((TypeError, Exception)):
            expl.title = "Changed"


# ============================================================================
# 4. ExplanationTemplates
# ============================================================================

class TestExplanationTemplates:
    def test_default_template(self):
        template = ExplanationTemplates.get_template("nonexistent")
        assert template["severity"] == "info"

    def test_task_failed_template(self):
        template = ExplanationTemplates.get_template("task.failed")
        assert template["severity"] == "error"
        assert "Task failed" in template["title"]

    def test_component_failed_template(self):
        template = ExplanationTemplates.get_template("component.failed")
        assert template["severity"] == "error"


# ============================================================================
# 5. ExplainabilityEngine
# ============================================================================

class TestExplainabilityEngine:
    def test_empty_telemetry_no_explanation(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = ExplainabilityEngine(svc)
        result = engine.explain_event("nonexistent")
        assert result is None

    def test_explain_single_event(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="SAM started",
        ))
        engine = ExplainabilityEngine(svc)
        events = svc.get_recent(1)
        result = engine.explain_event(events[0].id)
        assert result is not None
        assert result.title == "Runtime started"

    def test_explain_recent_returns_list(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RUNTIME_STARTED,
            component=Component.RUNTIME,
            category=EventCategory.LIFECYCLE,
            message="started",
        ))
        engine = ExplainabilityEngine(svc)
        results = engine.explain_recent()
        assert len(results) == 1

    def test_explain_task(self):
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_STARTED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            message="Task started",
            workflow_id="wf-test",
        ))
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_FAILED,
            component=Component.WORKFLOW,
            severity=EventSeverity.ERROR,
            category=EventCategory.EXECUTION,
            message="Connection timeout",
            workflow_id="wf-test",
        ))
        engine = ExplainabilityEngine(svc)
        result = engine.explain_task("wf-test")
        assert result is not None
        assert len(result.evidence) >= 2

    def test_template_task_failed_generates_reason(self):
        """Failed task explanation includes reason."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_FAILED,
            component=Component.WORKFLOW,
            severity=EventSeverity.ERROR,
            category=EventCategory.EXECUTION,
            message="Connection timeout",
            workflow_id="wf-1",
        ))
        engine = ExplainabilityEngine(svc)
        events = svc.get_recent(1)
        result = engine.explain_event(events[0].id)
        assert result is not None
        assert "fail" in result.why.lower() or "error" in result.why.lower()
        assert result.severity == ExplanationSeverity.ERROR

    def test_template_component_degraded(self):
        """Component degraded generates warning."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.COMPONENT_DEGRADED,
            component=Component.STORAGE,
            severity=EventSeverity.WARNING,
            category=EventCategory.SAFETY,
            message="Slow I/O",
        ))
        engine = ExplainabilityEngine(svc)
        events = svc.get_recent(1)
        result = engine.explain_event(events[0].id)
        assert result is not None
        assert result.severity == ExplanationSeverity.WARNING

    def test_explain_recent_empty(self):
        """Empty telemetry returns empty list."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = ExplainabilityEngine(svc)
        results = engine.explain_recent()
        assert results == []

    def test_explanation_has_impact_and_recommendation(self):
        """Explanation has impact and recommendation fields."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.COMPONENT_FAILED,
            component=Component.STORAGE,
            severity=EventSeverity.ERROR,
            category=EventCategory.SAFETY,
            message="Storage full",
        ))
        engine = ExplainabilityEngine(svc)
        events = svc.get_recent(1)
        result = engine.explain_event(events[0].id)
        assert result.impact is not None
        assert result.recommendation is not None

    def test_explain_task_not_found(self):
        """Non-existent task returns None."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = ExplainabilityEngine(svc)
        result = engine.explain_task("nonexistent")
        assert result is None
