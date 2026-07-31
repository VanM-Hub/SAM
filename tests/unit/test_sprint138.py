# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 138 - Mission Timeline tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.mission_runtime.timeline_checkpoint import TimelineCheckpoint
from sam.mission_runtime.mission_timeline import MissionTimeline
from sam.mission_runtime.timeline_builder import TimelineBuilder
from sam.mission_runtime.timeline_validator import (
    TimelineValidator,
    TimelineValidationReport,
)
from sam.mission_runtime.timeline_summary import TimelineSummary
from sam.mission_runtime.conversation_timeline import ConversationTimelineBridge
from sam.mission_runtime.dashboard_timeline import DashboardTimelineBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _timeline():
    return TimelineBuilder().build("m1", ("kickoff", "midpoint", "final"))


class TestCheckpointImmutable:
    def test_frozen(self):
        c = TimelineCheckpoint("c")
        with pytest.raises(FrozenInstanceError):
            c.order = 9


class TestTimelineImmutable:
    def test_frozen(self):
        t = MissionTimeline("m1")
        with pytest.raises(FrozenInstanceError):
            t.checkpoints = ()

    def test_count(self):
        assert _timeline().checkpoint_count == 3


class TestTimelineBuilder:
    def test_order(self):
        t = _timeline()
        assert t.checkpoints[0].order == 0
        assert t.checkpoints[2].label == "final"


class TestTimelineValidator:
    def test_valid(self):
        assert TimelineValidator().validate(_timeline()).valid is True

    def test_mismatch_invalid(self):
        t = MissionTimeline(
            "m1",
            (TimelineCheckpoint("a", order=5, label="x"),),
        )
        report = TimelineValidator().validate(t)
        assert report.valid is False
        assert report.issue_count == 1


class TestTimelineSummary:
    def test_summary(self):
        s = TimelineSummary("m1", ("a", "b"), total_checkpoints=2)
        assert s.total_checkpoints == 2

    def test_frozen(self):
        s = TimelineSummary("m1", ("a",))
        with pytest.raises(FrozenInstanceError):
            s.mission_id = "x"


# ---------- Conversation bridge ----------
class TestConversationTimelineBridge:
    def test_build(self):
        t = ConversationTimelineBridge().build("m1", ("a", "b"))
        assert t.checkpoint_count == 2

    def test_summarize(self):
        t = ConversationTimelineBridge().build("m1", ("a", "b", "c"))
        s = ConversationTimelineBridge().summarize(t)
        assert s.total_checkpoints == 3


# ---------- Dashboard bridge ----------
class TestDashboardTimelineBridge:
    def test_five_cards(self):
        cards = DashboardTimelineBridge().cards_for(_timeline())
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        b = DashboardTimelineBridge()
        assert "checkpoints" in b.verdict_card(_timeline()).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        TimelineCheckpoint,
        MissionTimeline,
        TimelineValidationReport,
        TimelineSummary,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
