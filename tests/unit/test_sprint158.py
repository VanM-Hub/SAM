"""Sprint 158 — Lifecycle State Machine Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.agent.state.agent_state import (
    AgentState, CREATED, PREPARING, RUNNING, WAITING,
    COMPLETED, CANCELLED, FAILED, ALL_STATES, TERMINAL_STATES,
)
from sam.agent.state.state_machine import StateMachine, TransitionResult
from sam.agent.state.transition_rule import TransitionRule
from sam.agent.state.transition_history import TransitionHistory, TransitionEvent
from sam.agent.state.state_validator import StateValidator, StateValidation
from sam.agent.state.conversation_state import ConversationStateBridge
from sam.agent.state.dashboard_state import DashboardStateBridge
from sam.agent.dashboard.agent_dashboard import ExecutionCard


class TestAgentState:
    def test_default_created(self):
        assert AgentState("m1").state == CREATED

    def test_terminal(self):
        assert AgentState("m1", COMPLETED).is_terminal() is True
        assert AgentState("m1", CANCELLED).is_terminal() is True
        assert AgentState("m1", FAILED).is_terminal() is True
        assert AgentState("m1", RUNNING).is_terminal() is False

    def test_valid_state(self):
        assert AgentState("m1", "Bogus").is_valid_state() is False

    def test_immutable(self):
        st = AgentState("m1")
        with pytest.raises(FrozenInstanceError):
            st.state = RUNNING


class TestLifecycleSets:
    def test_seven_states(self):
        assert ALL_STATES == {
            CREATED, PREPARING, RUNNING, WAITING,
            COMPLETED, CANCELLED, FAILED,
        }

    def test_terminal_set(self):
        assert TERMINAL_STATES == {COMPLETED, CANCELLED, FAILED}


class TestStateMachine:
    def _running(self):
        m = StateMachine()
        m.create("m1")
        m.transition("m1", PREPARING)
        m.transition("m1", RUNNING)
        return m

    def test_create(self):
        m = StateMachine()
        assert m.create("m1").state == CREATED

    def test_valid_sequence(self):
        m = self._running()
        assert m.current("m1").state == RUNNING

    def test_complete(self):
        m = self._running()
        r = m.transition("m1", COMPLETED)
        assert r.allowed is True
        assert m.current("m1").state == COMPLETED

    def test_terminal_blocked(self):
        m = self._running()
        m.transition("m1", COMPLETED)
        r = m.transition("m1", RUNNING)
        assert r.allowed is False

    def test_cancel_from_waiting(self):
        m = self._running()
        m.transition("m1", WAITING)
        assert m.transition("m1", CANCELLED).allowed is True

    def test_waiting_cycle(self):
        m = self._running()
        assert m.transition("m1", WAITING).allowed is True
        assert m.transition("m1", RUNNING).allowed is True

    def test_invalid_transition(self):
        m = self._running()
        r = m.transition("m1", CREATED)  # Running -> Created not allowed
        assert r.allowed is False

    def test_no_auto_retry(self):
        m = self._running()
        m.transition("m1", FAILED)
        r = m.transition("m1", RUNNING)  # no auto retry from Failed
        assert r.allowed is False

    def test_unknown_mission(self):
        m = StateMachine()
        r = m.transition("nope", RUNNING)
        assert r.allowed is False

    def test_noop_rejected(self):
        m = StateMachine()
        m.create("m1")
        r = m.transition("m1", CREATED)
        assert r.allowed is False

    def test_fail_from_preparing(self):
        m = StateMachine()
        m.create("m1")
        m.transition("m1", PREPARING)
        assert m.transition("m1", FAILED).allowed is True


class TestTransitionResult:
    def test_applied(self):
        assert TransitionResult("m1", True).applied is True
        assert TransitionResult("m1", False).applied is False

    def test_immutable(self):
        r = TransitionResult("m1", True)
        with pytest.raises(FrozenInstanceError):
            r.allowed = False


class TestTransitionRule:
    def test_no_auto_default(self):
        assert TransitionRule("A", "B").auto is False


class TestTransitionHistory:
    def test_record(self):
        h = TransitionHistory()
        h.record(TransitionEvent("m1", CREATED, RUNNING))
        assert h.count() == 1

    def test_filter(self):
        h = TransitionHistory()
        h.record(TransitionEvent("m1", "A", "B"))
        h.record(TransitionEvent("m2", "A", "B"))
        assert len(h.events("m1")) == 1

    def test_applied_count(self):
        h = TransitionHistory()
        h.record(TransitionEvent("m1", "A", "B", allowed=True))
        h.record(TransitionEvent("m1", "B", "C", allowed=False))
        assert h.applied_count() == 1


class TestStateValidator:
    def test_valid(self):
        v = StateValidator().validate(AgentState("m1", RUNNING))
        assert v.valid is True

    def test_invalid_state(self):
        v = StateValidator().validate(AgentState("m1", "Bogus"))
        assert v.valid is False


class TestConversationStateBridge:
    def test_show_current_state(self):
        m = StateMachine()
        m.create("m1")
        m.transition("m1", PREPARING)
        m.transition("m1", RUNNING)
        b = ConversationStateBridge(m)
        assert b.show_current_state("m1") == RUNNING

    def test_history(self):
        m = StateMachine()
        m.create("m1")
        h = TransitionHistory()
        h.record(TransitionEvent("m1", CREATED, RUNNING))
        b = ConversationStateBridge(m, h)
        assert b.show_transition_history("m1") == ["Created->Running"]

    def test_status(self):
        b = ConversationStateBridge(StateMachine())
        assert b.status() == "state machine ready"


class TestDashboardStateBridge:
    def test_five_cards(self):
        b = DashboardStateBridge(StateMachine())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardStateBridge(StateMachine())
        assert b.overview_card().verdict == "ready"


class TestStateImmutability:
    DTO_CLASSES = [
        AgentState, TransitionResult, TransitionRule,
        TransitionEvent, StateValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
