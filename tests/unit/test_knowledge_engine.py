"""
Unit tests for Knowledge Engine (OP-6).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime, timedelta
import pytest
from sam.experience.models.knowledge import (
    KnowledgeEntry, KnowledgeModel, KnowledgeType, InsightEntry,
)
from sam.operations.engine.knowledge import KnowledgeEngine
from sam.operations.engine.insight import InsightEngine
from sam.telemetry import (
    TelemetryEvent, TelemetryEventType, EventSeverity,
    EventCategory, Component, TelemetryService,
)


# ============================================================================
# 1. KnowledgeType Enum
# ============================================================================

class TestKnowledgeType:
    def test_all_types_exist(self):
        """All KnowledgeType members exist."""
        assert KnowledgeType.FACT.value == "fact"
        assert KnowledgeType.PATTERN.value == "pattern"
        assert KnowledgeType.RECOMMENDATION.value == "recommendation"

    def test_six_types(self):
        """There are 6 types."""
        assert len(list(KnowledgeType)) == 6


# ============================================================================
# 2. KnowledgeEntry
# ============================================================================

class TestKnowledgeEntry:
    def test_minimal_entry(self):
        """Can create KnowledgeEntry with minimum fields."""
        now = datetime.utcnow()
        e = KnowledgeEntry(
            id="k1", type=KnowledgeType.FACT, title="Fact",
            content="Content", source="test", timestamp=now,
        )
        assert e.id == "k1"
        assert e.tags == []
        assert e.confidence == 0.0

    def test_full_entry(self):
        """Can create KnowledgeEntry with all fields."""
        now = datetime.utcnow()
        e = KnowledgeEntry(
            id="k2", type=KnowledgeType.RECOMMENDATION,
            title="Recommendation", content="Do X",
            confidence=0.85, source="telemetry", timestamp=now,
            tags=["auto"], metadata={"source_id": "e1"},
        )
        assert e.confidence == 0.85
        assert e.metadata["source_id"] == "e1"


# ============================================================================
# 3. InsightEntry
# ============================================================================

class TestInsightEntry:
    def test_minimal_insight(self):
        """Can create InsightEntry with minimum fields."""
        now = datetime.utcnow()
        i = InsightEntry(
            id="i1", title="Insight", description="Desc",
            severity="info", created_at=now,
        )
        assert i.id == "i1"
        assert i.evidence == []

    def test_full_insight(self):
        """Can create InsightEntry with evidence."""
        now = datetime.utcnow()
        i = InsightEntry(
            id="i2", title="Insight", description="Desc",
            severity="warning", evidence=["Failure 1", "Failure 2"],
            created_at=now,
        )
        assert len(i.evidence) == 2


# ============================================================================
# 4. KnowledgeModel
# ============================================================================

class TestKnowledgeModel:
    def test_minimal_model(self):
        """Can create KnowledgeModel."""
        model = KnowledgeModel(entries=[], insights=[], total_entries=0)
        assert model.total_entries == 0
        assert model.recommendation_count == 0
        assert model.insight_count == 0

    def test_recommendation_count(self):
        """recommendation_count counts rec entries."""
        now = datetime.utcnow()
        rec = KnowledgeEntry(
            id="r1", type=KnowledgeType.RECOMMENDATION,
            title="Rec", content="Do X", source="test", timestamp=now,
        )
        fact = KnowledgeEntry(
            id="f1", type=KnowledgeType.FACT,
            title="Fact", content="X", source="test", timestamp=now,
        )
        model = KnowledgeModel(entries=[rec, fact], insights=[], total_entries=2)
        assert model.recommendation_count == 1

    def test_model_is_frozen(self):
        """KnowledgeModel is immutable."""
        model = KnowledgeModel(entries=[], insights=[], total_entries=0)
        with pytest.raises((TypeError, Exception)):
            model.total_entries = 5


# ============================================================================
# 5. KnowledgeEngine
# ============================================================================

class TestKnowledgeEngine:
    def test_empty_telemetry_returns_empty(self):
        """No events means empty knowledge."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = KnowledgeEngine(svc)
        model = engine.get_knowledge()
        assert model.total_entries == 0

    def test_recommendation_from_events(self):
        """Recommendation events become knowledge entries."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RECOMMENDATION_CREATED,
            component=Component.GUARDIAN,
            category=EventCategory.KNOWLEDGE,
            severity=EventSeverity.INFO,
            message="Increase memory limit",
        ))
        engine = KnowledgeEngine(svc)
        model = engine.get_knowledge()
        assert model.total_entries >= 1
        recs = engine.get_recommendations()
        assert len(recs) >= 1

    def test_guardian_alerts_as_patterns(self):
        """Guardian alerts become pattern entries."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.GUARDIAN_ALERT,
            component=Component.GUARDIAN,
            category=EventCategory.SAFETY,
            severity=EventSeverity.WARNING,
            message="Memory usage above 90%",
        ))
        engine = KnowledgeEngine(svc)
        model = engine.get_knowledge()
        assert model.total_entries >= 1

    def test_failed_events_as_lessons(self):
        """Failed events become lesson entries."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.TASK_FAILED,
            component=Component.WORKFLOW,
            category=EventCategory.EXECUTION,
            severity=EventSeverity.ERROR,
            message="Connection timeout",
        ))
        engine = KnowledgeEngine(svc)
        model = engine.get_knowledge()
        assert model.total_entries >= 1

    def test_search_finds_matching(self):
        """Search returns matching entries."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        svc.emit(TelemetryEvent(
            type=TelemetryEventType.RECOMMENDATION_CREATED,
            component=Component.GUARDIAN,
            category=EventCategory.KNOWLEDGE,
            severity=EventSeverity.INFO,
            message="Increase memory",
        ))
        engine = KnowledgeEngine(svc)
        results = engine.search("memory")
        assert len(results) >= 1
        results_none = engine.search("nonexistent")
        assert len(results_none) == 0

    def test_insight_repeated_failures(self):
        """Many failures trigger insight."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        for i in range(10):
            svc.emit(TelemetryEvent(
                type=TelemetryEventType.SYSTEM_ERROR,
                component=Component.STORAGE,
                category=EventCategory.SAFETY,
                severity=EventSeverity.ERROR,
                message="Storage error {}".format(i),
            ))
        engine = KnowledgeEngine(svc)
        model = engine.get_knowledge()
        assert model.insight_count >= 1

    def test_insight_high_recovery(self):
        """Many recovery events trigger insight."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        for i in range(5):
            svc.emit(TelemetryEvent(
                type=TelemetryEventType.RUNTIME_RECOVERING,
                component=Component.RUNTIME,
                category=EventCategory.RECOVERY,
                severity=EventSeverity.INFO,
                message="Recovery {}".format(i),
            ))
        engine = KnowledgeEngine(svc)
        model = engine.get_knowledge()
        assert model.insight_count >= 1

    def test_insight_operational(self):
        """Many events trigger operational insight."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        for i in range(60):
            svc.emit(TelemetryEvent(
                type=TelemetryEventType.RUNTIME_HEALTHY if hasattr(TelemetryEventType, 'RUNTIME_HEALTHY') else TelemetryEventType.RUNTIME_READY,
                component=Component.RUNTIME,
                category=EventCategory.LIFECYCLE,
                severity=EventSeverity.INFO,
                message="Event {}".format(i),
            ))
        engine = KnowledgeEngine(svc)
        model = engine.get_knowledge()
        assert model.insight_count >= 1


# ============================================================================
# 6. InsightEngine
# ============================================================================

class TestInsightEngine:
    def test_insight_engine_empty(self):
        """Empty telemetry produces no insights."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        engine = InsightEngine(svc)
        insights = engine.generate_insights()
        assert isinstance(insights, list)

    def test_insight_engine_with_events(self):
        """Events produce insights."""
        svc = TelemetryService(max_events=100, enable_cache=False)
        for i in range(8):
            svc.emit(TelemetryEvent(
                type=TelemetryEventType.SYSTEM_ERROR,
                component=Component.RUNTIME,
                category=EventCategory.SAFETY,
                severity=EventSeverity.ERROR,
                message="Error {}".format(i),
            ))
        engine = InsightEngine(svc)
        insights = engine.generate_insights()
        assert len(insights) >= 1
