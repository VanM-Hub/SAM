"""Sprint 157 — Mission Session Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.agent.session.mission_session import MissionSession
from sam.agent.session.mission_state import MissionState
from sam.agent.session.mission_context import MissionContext
from sam.agent.session.mission_snapshot import MissionSnapshot
from sam.agent.session.mission_registry import MissionRegistry, SessionSummary
from sam.agent.session.conversation_session import ConversationSessionBridge
from sam.agent.session.dashboard_session import DashboardSessionBridge
from sam.agent.dashboard.agent_dashboard import ExecutionCard


class TestMissionSession:
    def test_default(self):
        s = MissionSession("s1", "m1", "agent1")
        assert s.open is True
        assert s.external_calls == 0

    def test_to_dict(self):
        s = MissionSession("s1", "m1", "agent1")
        d = s.to_dict()
        assert d["mission_id"] == "m1"

    def test_immutable(self):
        s = MissionSession("s1", "m1", "agent1")
        with pytest.raises(FrozenInstanceError):
            s.open = False


class TestMissionState:
    def test_default(self):
        assert MissionState("m1").state == "Created"

    def test_immutable(self):
        st = MissionState("m1")
        with pytest.raises(FrozenInstanceError):
            st.state = "Running"


class TestMissionContext:
    def test_get(self):
        c = MissionContext("m1", data={"a": 1})
        assert c.get("a") == 1
        assert c.get("zzz") is None

    def test_readonly(self):
        assert MissionContext("m1").readonly is True

    def test_immutable(self):
        c = MissionContext("m1")
        with pytest.raises(FrozenInstanceError):
            c.agent_id = "x"


class TestMissionSnapshot:
    def test_default(self):
        assert MissionSnapshot("m1").state == "Created"


class TestMissionRegistry:
    def _reg(self):
        r = MissionRegistry()
        r.open_session(MissionSession("s1", "m1", "agent1"))
        r.set_state(MissionState("m1", "Running"))
        r.set_context(MissionContext("m1", agent_id="agent1"))
        r.record_snapshot(MissionSnapshot("m1", "Running", session_id="s1"))
        return r

    def test_session(self):
        r = self._reg()
        assert r.get_session("s1").mission_id == "m1"
        assert len(r.sessions_for_mission("m1")) == 1

    def test_state(self):
        r = self._reg()
        assert r.get_state("m1").state == "Running"

    def test_context(self):
        r = self._reg()
        assert r.get_context("m1").agent_id == "agent1"

    def test_snapshot(self):
        r = self._reg()
        assert len(r.snapshots("m1")) == 1
        assert r.count_missions() == 1

    def test_summary(self):
        r = self._reg()
        sm = r.session_summary()
        assert sm.total == 1
        assert sm.open == 1
        assert sm.total_external_calls == 0


class TestSessionSummary:
    def test_default(self):
        assert SessionSummary().total == 0


class TestConversationSessionBridge:
    def test_show_current_state(self):
        r = MissionRegistry()
        r.set_state(MissionState("m1", "Running"))
        b = ConversationSessionBridge(r)
        assert b.show_current_state("m1") == "Running"

    def test_show_summary(self):
        r = MissionRegistry()
        r.open_session(MissionSession("s1", "m1", "a1"))
        b = ConversationSessionBridge(r)
        assert b.show_summary()["total"] == 1

    def test_count(self):
        b = ConversationSessionBridge(MissionRegistry())
        assert b.count() == 0


class TestDashboardSessionBridge:
    def test_five_cards(self):
        r = MissionRegistry()
        r.open_session(MissionSession("s1", "m1", "a1"))
        b = DashboardSessionBridge(r)
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardSessionBridge(MissionRegistry())
        assert b.overview_card().verdict == "ready"


class TestSessionImmutability:
    DTO_CLASSES = [
        MissionSession, MissionState, MissionContext,
        MissionSnapshot, SessionSummary,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
