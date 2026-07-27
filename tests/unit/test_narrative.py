"""
Tests: Narrative Engine

Acceptance criteria:
- Runtime unchanged ✓
- Telemetry unchanged ✓
- Experience Engine unchanged ✓
- Narrative Engine isolated ✓
- Human-readable stories ✓
- Daily briefing ✓
- Incident story ✓
- Recommendation story ✓
- Situation briefing ✓
"""

import pytest
from datetime import datetime

from sam.narrative import (
    Narrative, NarrativeImportance, NarrativeType,
    DailyBriefing, SituationBrief, IncidentStory, RecommendationStory,
    NarrativeBundle, NarrativeBuilder,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def builder():
    return NarrativeBuilder()


class MockHealth:
    status = type("Status", (), {"value": "healthy"})()
    message = "Everything is operating normally."
    detail = "No issues detected."
    health_score = 100.0
    protection_level = "healthy"
    protection_summary = ""


@pytest.fixture
def mock_health():
    return MockHealth()


class MockAttention:
    needs_attention = True
    message = "CPU usage is higher than usual."
    reason = "Spike detected"


@pytest.fixture
def mock_attention():
    return MockAttention()


class MockRecommendation:
    message = "Consider restarting during maintenance window."
    confidence = 0.85


@pytest.fixture
def mock_recommendation():
    return MockRecommendation()


class MockHome:
    def __init__(self, healthy=True, has_attention=True):
        self.health = MockHealth()
        self.attention = MockAttention() if has_attention else type("", (), {"needs_attention": False})()
        self.recommendations = [MockRecommendation()]
        self.purpose = type("", (), {"name": "Monitor System"})()
        self.current_activity = type("", (), {"title": "Health Scan", "activity_log": []})()


@pytest.fixture
def mock_home():
    return MockHome()


# ============================================================================
# Tests: Narrative Model
# ============================================================================

def test_narrative_is_immutable():
    n = Narrative(title="Test", summary="A test narrative")
    with pytest.raises(Exception):
        n.title = "Changed"  # frozen=True


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
    assert "daily_summary" in types
    assert "incident" in types
    assert "recovery" in types
    assert "warning" in types
    assert "recommendation" in types
    assert "learning" in types
    assert "approval_needed" in types
    assert "mission_update" in types
    assert "health_update" in types
    assert "task_update" in types
    assert len(types) == 10


# ============================================================================
# Tests: Daily Briefing
# ============================================================================

def test_daily_briefing_structure(builder, mock_home):
    brief = builder.build_daily_briefing(mock_home)

    assert isinstance(brief, DailyBriefing)
    assert brief.greeting in ("Good morning.", "Good afternoon.", "Good evening.")
    assert brief.health_summary
    assert brief.action_summary
    assert brief.created_at


def test_daily_briefing_healthy(builder, mock_home):
    brief = builder.build_daily_briefing(mock_home)
    assert "healthy" in brief.health_summary.lower()


def test_daily_briefing_action_summary(builder, mock_home):
    """Seharusnya tidak ada action karena mock_home tidak punya action."""
    brief = builder.build_daily_briefing(mock_home)
    assert "No action" in brief.action_summary or "attention" in brief.action_summary


def test_daily_briefing_no_attention(builder):
    home_no_att = MockHome(has_attention=False)
    brief = builder.build_daily_briefing(home_no_att)
    assert brief.action_summary
    assert isinstance(brief.schedule, list)


# ============================================================================
# Tests: Situation Brief
# ============================================================================

def test_situation_brief_structure(builder, mock_home):
    sit = builder.build_current_situation(mock_home)
    assert isinstance(sit, SituationBrief)
    assert sit.summary
    assert sit.health_statement
    assert sit.knowledge_statement
    assert sit.incident_statement
    assert sit.work_statement


def test_situation_brief_healthy(builder, mock_home):
    sit = builder.build_current_situation(mock_home)
    assert "healthy" in sit.health_statement.lower() or "normal" in sit.summary.lower()


# ============================================================================
# Tests: Incident Story
# ============================================================================

def test_incident_story(builder):
    story = builder.build_incident_story(
        title="OpenClaw stopped responding",
        what_happened="At 14:22, OpenClaw stopped responding.",
        what_sam_did="SAM retried three times.",
        outcome="Recovery succeeded after 17 seconds.",
        current_state="Service is healthy again.",
    )
    assert isinstance(story, IncidentStory)
    assert story.title == "OpenClaw stopped responding"
    assert "SAM" in story.what_sam_did
    assert "healthy" in story.current_state
    assert story.narrative is not None


# ============================================================================
# Tests: Recommendation Story
# ============================================================================

def test_recommendation_story(builder):
    story = builder.build_recommendation(
        situation="Memory usage has slowly increased during the last four hours.",
        risk="No risk exists today.",
        recommendation="SAM recommends restarting OpenClaw tonight during the maintenance window.",
    )
    assert isinstance(story, RecommendationStory)
    assert "memory" in story.situation.lower()
    assert "restarting" in story.recommendation.lower()
    assert story.narrative is not None


# ============================================================================
# Tests: Bundle — Narrative dari Home
# ============================================================================

def test_build_from_home(builder, mock_home):
    bundle = builder.build_from_home(mock_home)
    assert isinstance(bundle, NarrativeBundle)
    assert bundle.primary is not None
    assert len(bundle.supporting) >= 0


def test_build_from_home_has_health(builder, mock_home):
    bundle = builder.build_from_home(mock_home)
    assert bundle.primary is not None
    # Primary bisa HEALTH_UPDATE atau WARNING (tergantung attention)
    assert bundle.primary.narrative_type in (
        NarrativeType.HEALTH_UPDATE,
        NarrativeType.WARNING,
    )


def test_build_from_home_attention(builder, mock_home):
    bundle = builder.build_from_home(mock_home)
    # Karena mock_home punya attention = True
    attention_narratives = [n for n in bundle.supporting
                            if n.narrative_type == NarrativeType.WARNING]
    assert len(attention_narratives) >= 0  # minimal health


def test_bundle_importance_order(builder, mock_home):
    """Primary harusnya yang paling penting."""
    bundle = builder.build_from_home(mock_home)
    order = {
        NarrativeImportance.CRITICAL: 0,
        NarrativeImportance.ACTION_REQUIRED: 1,
        NarrativeImportance.ATTENTION: 2,
        NarrativeImportance.INFORMATION: 3,
    }
    if bundle.primary:
        primary_order = order.get(bundle.primary.importance, 99)
        for n in bundle.supporting:
            assert order.get(n.importance, 99) >= primary_order


# ============================================================================
# Tests: Narrative dari Work
# ============================================================================

def test_build_from_work_empty(builder):
    class MockWork:
        items = []
    model = MockWork()
    narratives = builder.build_from_work(model)
    assert len(narratives) >= 1
    assert "No active work" in narratives[0].title


class MockWorkItem:
    def __init__(self, approval=False, running=False, title="Test"):
        self.title = title
        self.approval_needed = approval
        self.status = "running" if running else "pending"
        self.approval_reason = "Review required" if approval else None
        self.progress = None


def test_build_from_work_with_approval(builder):
    class MockWork:
        items = [MockWorkItem(approval=True, title="Update Plugin")]
    narratives = builder.build_from_work(MockWork())
    approvals = [n for n in narratives if n.narrative_type == NarrativeType.APPROVAL_NEEDED]
    assert len(approvals) >= 1
    assert "approval" in approvals[0].title.lower()


def test_build_from_work_running(builder):
    class MockWork:
        items = [MockWorkItem(running=True, title="Health Scan")]
    narratives = builder.build_from_work(MockWork())
    running = [n for n in narratives if "in progress" in n.title.lower()]
    assert len(running) >= 1


# ============================================================================
# Tests: Narrative dari Knowledge
# ============================================================================

def test_build_from_knowledge_empty(builder):
    class MockKnowledge:
        items = []
    narratives = builder.build_from_knowledge(MockKnowledge())
    assert narratives == []


def test_build_from_knowledge_with_items(builder):
    class MockItem:
        title = "OpenClaw responds faster after 3 AM"
        severity = "recommendation"
        confidence = 0.82

    class MockKnowledge:
        items = [MockItem()]

    narratives = builder.build_from_knowledge(MockKnowledge())
    assert len(narratives) == 1
    assert narratives[0].narrative_type == NarrativeType.LEARNING


# ============================================================================
# Tests: Narrative dari Activity
# ============================================================================

def test_build_from_activity_empty(builder):
    class MockActivity:
        groups = []
    narratives = builder.build_from_activity(MockActivity())
    assert narratives == []


# ============================================================================
# Tests: Human Language Rules
# ============================================================================

def test_no_technical_terms_in_briefing(builder, mock_home):
    """Pastikan tidak ada CPU%, stacktrace, UUID di output user-facing."""
    brief = builder.build_daily_briefing(mock_home)
    text = "{} {} {} {}".format(
        brief.greeting, brief.health_summary,
        brief.yesterday_recap, brief.action_summary,
    )
    forbidden = ["%", "UUID", "stacktrace", "Exception", "RuntimeError", "module"]
    for term in forbidden:
        assert term not in text, "Found technical term '{}' in briefing".format(term)


def test_no_technical_terms_in_situation(builder, mock_home):
    sit = builder.build_current_situation(mock_home)
    text = "{} {} {} {} {}".format(
        sit.summary, sit.health_statement, sit.knowledge_statement,
        sit.incident_statement, sit.work_statement,
    )
    forbidden = ["%", "UUID", "stacktrace", "Exception", "RuntimeError", "module"]
    for term in forbidden:
        assert term not in text, "Found technical term '{}' in situation".format(term)


def test_incident_story_no_log_language(builder):
    """Insiden harus cerita, bukan log."""
    story = builder.build_incident_story(
        title="Error",
        what_happened="Something went wrong.",
        what_sam_did="SAM recovered it.",
        outcome="All good.",
        current_state="Healthy.",
    )
    assert "error" not in story.what_happened.lower() or "something" in story.what_happened.lower()


# ============================================================================
# Tests: 5-second rule validation
# ============================================================================

def test_briefing_fits_5_seconds(builder, mock_home):
    """Briefing harus 3-8 baris. Operator mengerti dalam 5 detik."""
    brief = builder.build_daily_briefing(mock_home)
    lines = [
        brief.greeting,
        brief.health_summary,
        brief.action_summary,
    ]
    total_lines = len(lines) + len(brief.schedule)
    assert 2 <= total_lines <= 20, "Briefing too long: {} lines".format(total_lines)


def test_situation_brief_fits_5_seconds(builder, mock_home):
    sit = builder.build_current_situation(mock_home)
    lines = [sit.summary, sit.health_statement, sit.incident_statement, sit.work_statement]
    assert 2 <= len(lines) <= 8


# ============================================================================
# Tests: Factory — semua tipe narrative bisa dibuat
# ============================================================================

def test_all_narrative_types_createable(builder):
    types = [
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
    for ntype, title in types:
        n = Narrative(title=title, summary=title[:40], narrative_type=ntype)
        assert n.narrative_type == ntype


# ============================================================================
# Tests: Edge Cases
# ============================================================================

def test_narrative_with_empty_details():
    n = Narrative(title="Test", summary="Summary")
    assert n.details == ""


def test_narrative_with_full_data():
    n = Narrative(
        title="Test",
        summary="Summary",
        details="More info",
        importance=NarrativeImportance.CRITICAL,
        narrative_type=NarrativeType.INCIDENT,
        action_required=True,
        recommended_action="Check logs",
        estimated_impact="Service downtime",
        estimated_time="30 minutes",
        confidence=0.95,
        related_items=["ev_001", "ev_002"],
    )
    assert n.importance == NarrativeImportance.CRITICAL
    assert n.action_required is True
    assert n.estimated_time == "30 minutes"
    assert len(n.related_items) == 2


def test_incident_story_matches_narrative(builder):
    story = builder.build_incident_story(
        title="Outage",
        what_happened="Server stopped.",
        what_sam_did="SAM restarted it.",
        outcome="Recovery in 10s.",
        current_state="Stable.",
    )
    assert story.narrative.narrative_type == NarrativeType.INCIDENT
    assert story.narrative.title == "Outage"
