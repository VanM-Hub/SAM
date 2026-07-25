"""Tests for Cognitive Session — Sprint 29 Fase 5.

Coverage:
  - CognitiveSession creation, serialization, roundtrip
  - CognitiveSessionManager: start/get/update/end session
  - Active session tracking
  - add_reflection, add_decision
  - list_sessions by status
  - Integration with CognitiveManager
"""

import pytest
from datetime import datetime, timezone

from sam.cognition.session import (
    CognitiveSession,
    CognitiveSessionManager,
    SESSION_ACTIVE,
    SESSION_COMPLETED,
    SESSION_ABANDONED,
)
from sam.cognition.state import CognitiveState
from sam.cognition.context import ContextWindow
from sam.cognition.memory import WorkingMemoryManager
from sam.cognition.manager import CognitiveManager


# ── CognitiveSession Tests ────────────────────────────────────────


class TestCognitiveSession:
    def test_create_default(self):
        s = CognitiveSession()
        assert s.id.startswith("csess_")
        assert s.status == SESSION_ACTIVE
        assert s.reflection_ids == []
        assert s.decisions == []
        assert s.working_memory_snapshot == {}
        assert s.ended_at is None

    def test_create_with_fields(self):
        state = CognitiveState(health=85.0, focus="latency")
        s = CognitiveSession(
            goal_id="goal_001",
            intent_id="int_002",
            state=state,
            working_memory_snapshot={"cpu": 80},
            reflection_ids=["refl_1"],
            decisions=[{"type": "scale"}],
        )
        assert s.goal_id == "goal_001"
        assert s.intent_id == "int_002"
        assert s.state.health == 85.0
        assert s.working_memory_snapshot["cpu"] == 80
        assert "refl_1" in s.reflection_ids
        assert s.decisions[0]["type"] == "scale"

    def test_to_dict(self):
        s = CognitiveSession(goal_id="g1")
        d = s.to_dict()
        assert d["goal_id"] == "g1"
        assert d["status"] == SESSION_ACTIVE
        assert d["ended_at"] is None

    def test_from_dict_roundtrip(self):
        state = CognitiveState(health=70.0, confidence=65.0)
        s = CognitiveSession(
            goal_id="g1",
            intent_id="i1",
            state=state,
            working_memory_snapshot={"queue": 5},
            reflection_ids=["r1", "r2"],
            decisions=[{"type": "heal", "action": "restart"}],
        )
        d = s.to_dict()
        s2 = CognitiveSession.from_dict(d)
        assert s2.goal_id == s.goal_id
        assert s2.intent_id == s.intent_id
        assert s2.state.health == s.state.health
        assert s2.working_memory_snapshot["queue"] == 5
        assert s2.reflection_ids == ["r1", "r2"]
        assert s2.decisions[0]["type"] == "heal"

    def test_from_dict_empty(self):
        s = CognitiveSession.from_dict({})
        assert s.status == SESSION_ACTIVE
        assert s.reflection_ids == []

    def test_repr(self):
        s = CognitiveSession()
        r = repr(s)
        assert "CognitiveSession" in r
        assert "ACTIVE" in r


# ── CognitiveSessionManager Tests ─────────────────────────────────


class TestCognitiveSessionManager:
    @pytest.fixture
    def mgr(self):
        return CognitiveSessionManager()

    async def test_start_session_returns_id(self, mgr):
        sid = await mgr.start_session()
        assert sid.startswith("csess_")

    async def test_start_session_with_goal_and_intent(self, mgr):
        sid = await mgr.start_session(goal_id="g1", intent_id="i1")
        session = await mgr.get_session(sid)
        assert session.goal_id == "g1"
        assert session.intent_id == "i1"

    async def test_start_session_with_state(self, mgr):
        state = CognitiveState(health=80.0, focus="availability")
        sid = await mgr.start_session(state=state)
        session = await mgr.get_session(sid)
        assert session.state.health == 80.0
        assert session.state.focus == "availability"

    async def test_get_session_nonexistent(self, mgr):
        assert await mgr.get_session("ghost") is None

    async def test_update_session_goal(self, mgr):
        sid = await mgr.start_session()
        await mgr.update_session(sid, {"goal_id": "new_goal"})
        session = await mgr.get_session(sid)
        assert session.goal_id == "new_goal"

    async def test_update_session_nonexistent(self, mgr):
        # Should not raise
        await mgr.update_session("ghost", {"goal_id": "x"})

    async def test_end_session_completed(self, mgr):
        sid = await mgr.start_session()
        await mgr.end_session(sid, status=SESSION_COMPLETED)
        session = await mgr.get_session(sid)
        assert session.status == SESSION_COMPLETED
        assert session.ended_at is not None

    async def test_end_session_abandoned(self, mgr):
        sid = await mgr.start_session()
        await mgr.end_session(sid, status=SESSION_ABANDONED)
        session = await mgr.get_session(sid)
        assert session.status == SESSION_ABANDONED

    async def test_end_session_nonexistent(self, mgr):
        await mgr.end_session("ghost")  # Should not raise

    async def test_get_active_session(self, mgr):
        sid = await mgr.start_session()
        active = await mgr.get_active_session()
        assert active is not None
        assert active.id == sid

    async def test_get_active_session_none(self, mgr):
        active = await mgr.get_active_session()
        assert active is None

    async def test_get_active_session_after_end(self, mgr):
        sid = await mgr.start_session()
        await mgr.end_session(sid)
        active = await mgr.get_active_session()
        assert active is None

    async def test_add_reflection(self, mgr):
        sid = await mgr.start_session()
        await mgr.add_reflection(sid, "refl_001")
        session = await mgr.get_session(sid)
        assert "refl_001" in session.reflection_ids

    async def test_add_reflection_dedup(self, mgr):
        sid = await mgr.start_session()
        await mgr.add_reflection(sid, "refl_001")
        await mgr.add_reflection(sid, "refl_001")  # Same ID
        session = await mgr.get_session(sid)
        assert len(session.reflection_ids) == 1

    async def test_add_reflection_nonexistent_session(self, mgr):
        await mgr.add_reflection("ghost", "r1")  # Should not raise

    async def test_add_decision(self, mgr):
        sid = await mgr.start_session()
        await mgr.add_decision(sid, {"type": "scale", "workers": 5})
        session = await mgr.get_session(sid)
        assert len(session.decisions) == 1
        assert session.decisions[0]["type"] == "scale"

    async def test_add_multiple_decisions(self, mgr):
        sid = await mgr.start_session()
        await mgr.add_decision(sid, {"type": "heal"})
        await mgr.add_decision(sid, {"type": "optimize"})
        session = await mgr.get_session(sid)
        assert len(session.decisions) == 2

    async def test_add_decision_nonexistent_session(self, mgr):
        await mgr.add_decision("ghost", {"type": "x"})  # Should not raise

    async def test_list_sessions(self, mgr):
        s1 = await mgr.start_session(goal_id="g1")
        s2 = await mgr.start_session(goal_id="g2")
        sessions = await mgr.list_sessions()
        assert len(sessions) == 2
        # Both sessions should be present (order depends on sort timing)
        ids = {s.id for s in sessions}
        assert s1 in ids
        assert s2 in ids
        # Last session should be first (newest first)
        assert sessions[0].id == s2

    async def test_list_sessions_filter_active(self, mgr):
        s1 = await mgr.start_session(goal_id="g1")
        s2 = await mgr.start_session(goal_id="g2")
        await mgr.end_session(s1)
        active = await mgr.list_sessions(status_filter=SESSION_ACTIVE)
        assert len(active) == 1
        assert active[0].id == s2

    async def test_list_sessions_filter_completed(self, mgr):
        s1 = await mgr.start_session()
        s2 = await mgr.start_session()
        await mgr.end_session(s1)
        completed = await mgr.list_sessions(status_filter=SESSION_COMPLETED)
        assert len(completed) == 1

    async def test_clear(self, mgr):
        await mgr.start_session()
        await mgr.start_session()
        await mgr.clear()
        assert await mgr.list_sessions() == []
        assert await mgr.get_active_session() is None


# ── Integration with CognitiveManager ─────────────────────────────


class TestIntegration:
    @pytest.fixture
    def cm(self):
        return CognitiveManager()

    async def test_start_session_via_manager(self, cm):
        sid = await cm.start_session(goal_id="g1")
        assert sid.startswith("csess_")
        session = await cm.get_session(sid)
        assert session.goal_id == "g1"

    async def test_session_captures_current_state(self, cm):
        await cm.update_state({"health": 75.0, "focus": "latency"})
        sid = await cm.start_session()
        session = await cm.get_session(sid)
        assert session.state.health == 75.0
        assert session.state.focus == "latency"

    async def test_session_captures_wm_snapshot(self, cm):
        await cm.wm_set("cpu_usage", 85.0)
        sid = await cm.start_session()
        session = await cm.get_session(sid)
        assert session.working_memory_snapshot.get("cpu_usage") == 85.0

    async def test_end_session_via_manager(self, cm):
        sid = await cm.start_session()
        await cm.end_session(sid)
        session = await cm.get_session(sid)
        assert session.status == SESSION_COMPLETED

    async def test_add_reflection_via_manager(self, cm):
        sid = await cm.start_session()
        await cm.add_reflection_to_session(sid, "refl_abc")
        session = await cm.get_session(sid)
        assert "refl_abc" in session.reflection_ids

    async def test_add_decision_via_manager(self, cm):
        sid = await cm.start_session()
        await cm.add_decision_to_session(sid, {"type": "heal", "action": "restart"})
        session = await cm.get_session(sid)
        assert len(session.decisions) == 1

    async def test_active_session_via_manager(self, cm):
        sid = await cm.start_session()
        active = await cm.get_active_session()
        assert active is not None
        assert active.id == sid

    async def test_context_window_via_manager(self, cm):
        await cm.ctx_set("symptom", "high latency", importance=0.9)
        await cm.ctx_set("hypothesis", "network issue", importance=0.7)
        items = await cm.ctx_list(min_importance=0.6)
        assert len(items) == 2
        snap = await cm.ctx_snapshot()
        assert snap["symptom"] == "high latency"

    async def test_context_prune_via_manager(self, cm):
        await cm.ctx_set("keep", "alive", importance=0.9)
        await cm.ctx_set("trash", "gone", importance=0.01)
        removed = await cm.ctx_prune()
        assert removed == 1
        assert await cm.ctx_get("keep") == "alive"
        assert await cm.ctx_get("trash") is None

    async def test_full_cognitive_cycle(self, cm):
        """Simulate a full cognitive reasoning cycle."""
        # 1. Update state
        await cm.update_state({"health": 80.0, "confidence": 75.0})

        # 2. Store context
        await cm.ctx_set("current_symptom", "error_rate_increase", importance=0.9)
        await cm.ctx_set("active_hypothesis", "provider_timeout", importance=0.8)

        # 3. Update working memory
        await cm.wm_set("cpu_usage", 85.0)

        # 4. Start session
        sid = await cm.start_session(goal_id="heal_001")

        # 5. Add decision
        await cm.add_decision_to_session(sid, {"type": "heal", "action": "retry"})

        # 6. Add reflection
        await cm.add_reflection_to_session(sid, "refl_001")

        # 7. End session
        await cm.end_session(sid, "COMPLETED")

        # Verify
        session = await cm.get_session(sid)
        assert session.status == "COMPLETED"
        assert len(session.decisions) == 1
        assert "refl_001" in session.reflection_ids
        assert session.state.health == 80.0

    async def test_list_sessions_via_manager(self, cm):
        await cm.start_session()
        await cm.start_session()
        sessions = await cm.list_sessions()
        assert len(sessions) == 2
