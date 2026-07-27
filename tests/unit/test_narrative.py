"""
Tests: Model layer (ex-NarrativeEngine — migrated to ops/models)
"""

import pytest
from datetime import datetime

from sam.operations.models import (
    Narrative, NarrativeImportance, NarrativeType,
)


# ============================================================================
# Tests: Narrative Model
# ============================================================================

def test_narrative_is_immutable():
    n = Narrative(title="Test", summary="A test narrative")
    with pytest.raises(Exception):
        n.title = "Changed"


def test_narrative_defaults():
    n = Narrative(title="Test", summary="A test narrative")
    assert n.importance == NarrativeImportance.INFORMATION
    assert n.narrative_type == NarrativeType.HEALTH_UPDATE
    assert n.action_required is False
    assert n.confidence == 1.0
    assert n.related_items == []


def test_narrative_importance_enum():
    assert NarrativeImportance.INFORMATION.value == "information"
    assert NarrativeImportance.ATTENTION.value == "attention"
    assert NarrativeImportance.ACTION_REQUIRED.value == "action_required"
    assert NarrativeImportance.CRITICAL.value == "critical"


def test_narrative_types():
    types = [t.value for t in NarrativeType]
    assert len(types) >= 10
    assert "health_update" in types
    assert "incident" in types
    assert "recommendation" in types
    assert "learning" in types
    assert "approval_needed" in types


def test_narrative_with_empty_details():
    n = Narrative(title="Test", summary="Summary")
    assert n.details == ""


def test_narrative_with_full_data():
    n = Narrative(
        title="Outage detected",
        summary="Service experienced a brief interruption",
        details="Duration: 2m 14s",
        importance=NarrativeImportance.CRITICAL,
        narrative_type=NarrativeType.INCIDENT,
        action_required=True,
        recommended_action="Review deployment logs",
        estimated_impact="None — auto-recovered",
        estimated_time="2 minutes",
        confidence=0.85,
        related_items=["dep_001", "hck_002"],
    )
    assert n.importance == NarrativeImportance.CRITICAL
    assert n.narrative_type == NarrativeType.INCIDENT
    assert n.action_required is True
    assert len(n.related_items) == 2


def test_all_narrative_types_createable():
    types_data = [
        (NarrativeType.DAILY_SUMMARY, "Daily summary"),
        (NarrativeType.INCIDENT, "Incident occurred"),
        (NarrativeType.RECOVERY, "Recovery completed"),
        (NarrativeType.WARNING, "Warning issued"),
        (NarrativeType.RECOMMENDATION, "Recommended action"),
        (NarrativeType.LEARNING, "Learned something"),
        (NarrativeType.APPROVAL_NEEDED, "Approval pending"),
        (NarrativeType.MISSION_UPDATE, "Mission updated"),
        (NarrativeType.HEALTH_UPDATE, "Health changed"),
        (NarrativeType.TASK_UPDATE, "Task updated"),
    ]
    for ntype, title in types_data:
        n = Narrative(title=title, summary=title[:40], narrative_type=ntype)
        assert n.narrative_type == ntype
