# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 129 - Coordination tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.coordination_state import CoordinationState
from sam.orchestrator.coordination_report import CoordinationReport
from sam.orchestrator.coordination_validator import CoordinationValidator, CoordinationValidationReport
from sam.orchestrator.coordination_history import CoordinationHistory
from sam.orchestrator.runtime_coordinator import RuntimeCoordinator
from sam.orchestrator.conversation_coordination import ConversationCoordinationBridge
from sam.orchestrator.dashboard_coordination import DashboardCoordinationBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestStateImmutable:
    def test_frozen(self):
        s = CoordinationState("r")
        with pytest.raises(FrozenInstanceError):
            s.state = "ready"

    def test_properties(self):
        assert CoordinationState("r", state="ready").is_ready is True
        assert CoordinationState("r", state="coordinated").is_coordinated is True


class TestReportImmutable:
    def test_frozen(self):
        r = CoordinationReport()
        with pytest.raises(FrozenInstanceError):
            r.states = ()

    def test_all_coordinated(self):
        r = CoordinationReport(
            states=(CoordinationState("a", "coordinated"), CoordinationState("b", "coordinated"))
        )
        assert r.all_coordinated is True
        assert r.coordinated_count == 2

    def test_partial(self):
        r = CoordinationReport(states=(CoordinationState("a", "ready"),))
        assert r.all_coordinated is False


class TestRuntimeCoordinator:
    def test_coordinate(self):
        report = RuntimeCoordinator().coordinate(("a", "b", "c"))
        assert report.coordinated_count == 3
        assert report.all_coordinated is True

    def test_step_order(self):
        report = RuntimeCoordinator().coordinate(("a", "b"))
        assert report.states[1].step == 1


class TestCoordinationValidator:
    def test_valid(self):
        r = RuntimeCoordinator().coordinate(("a", "b"))
        assert CoordinationValidator().validate(r).valid is True

    def test_invalid_state(self):
        r = CoordinationReport(states=(CoordinationState("a", "bogus"),))
        report = CoordinationValidator().validate(r)
        assert report.valid is False
        assert report.issue_count == 1


class TestCoordinationHistory:
    def test_record_count(self):
        h = CoordinationHistory()
        h.record(CoordinationState("a"))
        h.record(CoordinationState("b"))
        assert h.count() == 2

    def test_clear(self):
        h = CoordinationHistory()
        h.record(CoordinationState("a"))
        h.clear()
        assert h.count() == 0


# ---------- Conversation bridge ----------
class TestConversationCoordinationBridge:
    def test_coordinate(self):
        b = ConversationCoordinationBridge(RuntimeCoordinator())
        report = b.coordinate(("a", "b", "c"))
        assert b.coordinated(report) == 3


# ---------- Dashboard bridge ----------
class TestDashboardCoordinationBridge:
    def test_five_cards(self):
        r = RuntimeCoordinator().coordinate(("a", "b"))
        cards = DashboardCoordinationBridge().cards_for(r)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        r = RuntimeCoordinator().coordinate(("a",))
        b = DashboardCoordinationBridge()
        assert "harmonized" in b.verdict_card(r).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        CoordinationState,
        CoordinationReport,
        CoordinationValidationReport,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
