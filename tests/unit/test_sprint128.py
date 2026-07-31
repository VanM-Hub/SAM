# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 128 - Scheduling tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.schedule_request import ScheduleRequest
from sam.orchestrator.schedule_plan import SchedulePlan
from sam.orchestrator.schedule_validator import ScheduleValidator, ScheduleValidationReport
from sam.orchestrator.schedule_registry import ScheduleRegistry, ScheduleRegistrationResult
from sam.orchestrator.schedule_summary import ScheduleSummary
from sam.orchestrator.conversation_schedule import ConversationScheduleBridge
from sam.orchestrator.dashboard_schedule import DashboardScheduleBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestScheduleRequestImmutable:
    def test_frozen(self):
        r = ScheduleRequest("s")
        with pytest.raises(FrozenInstanceError):
            r.priority = 1


class TestSchedulePlanImmutable:
    def test_frozen(self):
        p = SchedulePlan("s")
        with pytest.raises(FrozenInstanceError):
            p.order = ()


class TestScheduleValidator:
    def test_valid(self):
        p = SchedulePlan("s", ("a", "b", "c"))
        assert ScheduleValidator().validate(p).valid is True

    def test_empty_invalid(self):
        p = SchedulePlan("s")
        assert ScheduleValidator().validate(p).valid is False

    def test_duplicate_invalid(self):
        p = SchedulePlan("s", ("a", "a"))
        report = ScheduleValidator().validate(p)
        assert report.valid is False
        assert report.issue_count == 1


class TestScheduleRegistry:
    def test_register_and_get(self):
        reg = ScheduleRegistry()
        res = reg.register(ScheduleRequest("s1", ("a", "b")), ("a", "b"))
        assert res.accepted is True
        assert reg.get("s1").stage_count == 2

    def test_count(self):
        reg = ScheduleRegistry()
        reg.register(ScheduleRequest("s1"), ("a",))
        reg.register(ScheduleRequest("s2"), ("b",))
        assert reg.count() == 2


class TestScheduleSummary:
    def test_summary(self):
        s = ScheduleSummary("s", ("a", "b"), total_stages=2)
        assert s.total_stages == 2

    def test_frozen(self):
        s = ScheduleSummary("s", ("a",))
        with pytest.raises(FrozenInstanceError):
            s.schedule_id = "x"


# ---------- Conversation bridge ----------
class TestConversationScheduleBridge:
    def test_locate(self):
        reg = ScheduleRegistry()
        reg.register(ScheduleRequest("s1", ("a", "b")), ("a", "b"))
        b = ConversationScheduleBridge(reg)
        assert b.locate("s1").order == ("a", "b")

    def test_count(self):
        reg = ScheduleRegistry()
        reg.register(ScheduleRequest("s1"), ("a",))
        assert ConversationScheduleBridge(reg).count() == 1


# ---------- Dashboard bridge ----------
class TestDashboardScheduleBridge:
    def test_five_cards(self):
        p = SchedulePlan("s", ("a", "b", "c"))
        cards = DashboardScheduleBridge().cards_for(p)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        p = SchedulePlan("s", ("a",))
        b = DashboardScheduleBridge()
        assert "order" in b.verdict_card(p).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        ScheduleRequest,
        SchedulePlan,
        ScheduleSummary,
        ScheduleValidationReport,
        ScheduleRegistrationResult,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
