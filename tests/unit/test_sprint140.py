# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 140 - Mission Coordination tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.mission_runtime.coordination_plan import CoordinationPlan
from sam.mission_runtime.coordination_summary import CoordinationSummary
from sam.mission_runtime.coordination_registry import (
    CoordinationRegistry,
    CoordinationRegistrationResult,
)
from sam.mission_runtime.coordination_validator import (
    CoordinationValidator,
    CoordinationValidationReport,
)
from sam.mission_runtime.mission_coordinator import MissionCoordinator
from sam.mission_runtime.conversation_coordination import ConversationCoordinationBridge
from sam.mission_runtime.dashboard_coordination import DashboardCoordinationBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestPlanImmutable:
    def test_frozen(self):
        p = CoordinationPlan("m")
        with pytest.raises(FrozenInstanceError):
            p.runtimes = ()

    def test_plan_only(self):
        assert CoordinationPlan("m").is_plan_only is True

    def test_count(self):
        p = CoordinationPlan("m", ("a", "b", "c"))
        assert p.runtime_count == 3


class TestCoordinator:
    def test_coordinate(self):
        reg = CoordinationRegistry()
        c = MissionCoordinator(reg)
        plan = c.coordinate("m", ("a", "b"))
        assert plan.runtime_count == 2
        assert reg.count() == 1


class TestCoordinationRegistry:
    def test_get(self):
        reg = CoordinationRegistry()
        MissionCoordinator(reg).coordinate("m", ("a",))
        assert reg.get("m").runtime_count == 1


class TestCoordinationValidator:
    def test_valid(self):
        p = CoordinationPlan("m", ("a", "b"))
        assert CoordinationValidator().validate(p).valid is True

    def test_duplicate_invalid(self):
        p = CoordinationPlan("m", ("a", "a"))
        report = CoordinationValidator().validate(p)
        assert report.valid is False
        assert report.issue_count == 1


class TestCoordinationSummary:
    def test_summary(self):
        s = CoordinationSummary("m", ("a",), total=1)
        assert s.total == 1

    def test_frozen(self):
        s = CoordinationSummary("m", ("a",))
        with pytest.raises(FrozenInstanceError):
            s.mission_id = "x"


# ---------- Conversation bridge ----------
class TestConversationCoordinationBridge:
    def test_coordinate_plan(self):
        reg = CoordinationRegistry()
        b = ConversationCoordinationBridge(MissionCoordinator(reg))
        plan = b.coordinate("m", ("a", "b"))
        assert b.plan_of("m").runtime_count == 2


# ---------- Dashboard bridge ----------
class TestDashboardCoordinationBridge:
    def test_five_cards(self):
        plan = CoordinationPlan("m", ("a", "b"))
        cards = DashboardCoordinationBridge().cards_for(plan)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        plan = CoordinationPlan("m", ("a",))
        b = DashboardCoordinationBridge()
        assert "coordinated" in b.verdict_card(plan).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        CoordinationPlan,
        CoordinationSummary,
        CoordinationRegistrationResult,
        CoordinationValidationReport,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
