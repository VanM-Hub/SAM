# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 139 - Mission State tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.mission_runtime.mission_state import MissionState
from sam.mission_runtime.state_transition import StateTransition
from sam.mission_runtime.state_registry import StateRegistry, StateRegistrationResult
from sam.mission_runtime.state_validator import StateValidator, StateValidationReport
from sam.mission_runtime.state_history import StateHistory
from sam.mission_runtime.conversation_state import ConversationStateBridge
from sam.mission_runtime.dashboard_state import DashboardStateBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestStateImmutable:
    def test_frozen(self):
        s = MissionState("m")
        with pytest.raises(FrozenInstanceError):
            s.state = "closed"

    def test_properties(self):
        assert MissionState("m", "open").is_open is True
        assert MissionState("m", "active").is_active is True
        assert MissionState("m", "closed").is_closed is True


class TestTransitionImmutable:
    def test_frozen(self):
        t = StateTransition("m", "open", "closed")
        with pytest.raises(FrozenInstanceError):
            t.to_state = "x"

    def test_changed(self):
        assert StateTransition("m", "open", "closed").changed is True
        assert StateTransition("m", "open", "open").changed is False


class TestStateRegistry:
    def test_set_get(self):
        r = StateRegistry()
        r.set(MissionState("m", "active"))
        assert r.get("m").is_active is True

    def test_count(self):
        r = StateRegistry()
        r.set(MissionState("a"))
        r.set(MissionState("b"))
        assert r.count() == 2


class TestStateValidator:
    def test_valid(self):
        assert StateValidator().validate_state(MissionState("m", "active")).valid is True

    def test_invalid_state(self):
        report = StateValidator().validate_state(MissionState("m", "bogus"))
        assert report.valid is False
        assert report.issue_count == 1

    def test_valid_transition(self):
        t = StateTransition("m", "open", "active")
        assert StateValidator().validate_transition(t).valid is True


class TestStateHistory:
    def test_record(self):
        h = StateHistory()
        h.record(StateTransition("m", "open", "active"))
        assert h.count() == 1

    def test_clear(self):
        h = StateHistory()
        h.record(StateTransition("m", "open", "active"))
        h.clear()
        assert h.count() == 0


# ---------- Conversation bridge ----------
class TestConversationStateBridge:
    def test_open_transition(self):
        b = ConversationStateBridge(StateRegistry(), StateHistory())
        b.open("m")
        b.transition("m", "active")
        assert b.state_of("m").is_active is True

    def test_history_tracked(self):
        b = ConversationStateBridge(StateRegistry(), StateHistory())
        b.open("m")
        b.transition("m", "active")
        b.transition("m", "closed")
        assert b.summary()["transitions"] == 2


# ---------- Dashboard bridge ----------
class TestDashboardStateBridge:
    def test_five_cards(self):
        cards = DashboardStateBridge().cards_for(MissionState("m", "active"))
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        b = DashboardStateBridge()
        assert "state" in b.verdict_card(MissionState("m")).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [MissionState, StateTransition, StateRegistrationResult, StateValidationReport]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
