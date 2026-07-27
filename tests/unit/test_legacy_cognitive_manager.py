"""Tests for Cognitive Manager — Sprint 29 Fase 1.

Coverage:
  - CognitiveManager orchestration of state + memory
  - Combined operations: refresh_state_from_working_memory
"""

import pytest

from sam.cognition.manager import CognitiveManager
from sam.cognition.state import CognitiveStateManager
from sam.cognition.memory import WorkingMemoryManager


class TestCognitiveManager:
    @pytest.fixture
    def cm(self):
        return CognitiveManager()

    async def test_get_state_defaults(self, cm):
        state = await cm.get_current_state()
        assert state.health == 100.0
        assert state.focus == "balanced"

    async def test_update_state(self, cm):
        await cm.update_state({"health": 80.0, "focus": "latency"})
        state = await cm.get_current_state()
        assert state.health == 80.0
        assert state.focus == "latency"

    async def test_get_state_alias(self, cm):
        state = await cm.get_state()
        assert state.health == 100.0

    async def test_wm_set_and_get(self, cm):
        await cm.wm_set("key1", "value1")
        val = await cm.wm_get("key1")
        assert val == "value1"

    async def test_wm_delete(self, cm):
        await cm.wm_set("k", "v")
        await cm.wm_delete("k")
        assert await cm.wm_get("k") is None

    async def test_wm_clear(self, cm):
        await cm.wm_set("a", 1)
        await cm.wm_set("b", 2)
        await cm.wm_clear()
        assert await cm.wm_get("a") is None

    async def test_wm_snapshot(self, cm):
        await cm.wm_set("x", 100)
        snap = await cm.wm_snapshot()
        assert snap["x"] == 100

    async def test_wm_snapshot_with_session(self, cm):
        await cm.wm_set("k", "v1", session_id="s1")
        await cm.wm_set("k", "v2", session_id="s2")
        snap = await cm.wm_snapshot_all()
        assert snap["s1"]["k"] == "v1"
        assert snap["s2"]["k"] == "v2"

    async def test_wm_list_sessions(self, cm):
        await cm.wm_set("k", "v", session_id="alpha")
        await cm.wm_set("k", "v", session_id="beta")
        sessions = await cm.wm_list_sessions()
        assert set(sessions) == {"alpha", "beta"}

    async def test_get_state_history(self, cm):
        await cm.update_state({"health": 90.0})
        await cm.update_state({"health": 80.0})
        history = await cm.get_state_history(limit=10)
        assert len(history) == 2

    async def test_refresh_state_from_working_memory_noop(self, cm):
        """No values in WM -> no state change."""
        state = await cm.refresh_state_from_working_memory()
        assert state.health == 100.0  # unchanged

    async def test_refresh_state_from_working_memory_applies(self, cm):
        """Values in WM -> state updated."""
        await cm.wm_set("health", 55.0)
        await cm.wm_set("focus", "security")
        state = await cm.refresh_state_from_working_memory()
        assert state.health == 55.0
        assert state.focus == "security"

    async def test_refresh_with_multiple_fields(self, cm):
        await cm.wm_set("health", 70.0)
        await cm.wm_set("confidence", 60.0)
        await cm.wm_set("risk", 25.0)
        await cm.wm_set("autonomy_level", 3)
        state = await cm.refresh_state_from_working_memory()
        assert state.health == 70.0
        assert state.confidence == 60.0
        assert state.risk == 25.0
        assert state.autonomy_level == 3

    async def test_refresh_partial_update(self, cm):
        """Only some fields in WM -> only those updated."""
        await cm.wm_set("health", 42.0)
        state = await cm.refresh_state_from_working_memory()
        assert state.health == 42.0
        assert state.confidence == 100.0  # unchanged default

    async def test_refresh_with_session(self, cm):
        await cm.wm_set("health", 88.0, session_id="worker_1")
        state = await cm.refresh_state_from_working_memory(session_id="worker_1")
        assert state.health == 88.0

    async def test_constructor_with_custom_managers(self):
        sm = CognitiveStateManager()
        wm = WorkingMemoryManager()
        cm = CognitiveManager(state_manager=sm, working_memory_manager=wm)
        assert cm._state is sm
        assert cm._memory is wm
