"""Tests for Cognitive State — Sprint 29 Fase 1.

Coverage:
  - CognitiveState creation and field validation
  - CognitiveStateManager: get/update/history
  - Allowed focus values, clamping, serialization
"""

import json
from datetime import datetime, timezone

import pytest

from sam.cognition.state import (
    CognitiveState,
    CognitiveStateManager,
    ALLOWED_FOCUS_VALUES,
)


# ── CognitiveState Unit Tests ─────────────────────────────────────


class TestCognitiveState:
    def test_create_default(self):
        s = CognitiveState()
        assert s.id is not None and s.id.startswith("cs_")
        assert s.health == 100.0
        assert s.confidence == 100.0
        assert s.focus == "balanced"
        assert s.risk == 0.0
        assert s.autonomy_level == 2
        assert s.learning_objective == ""
        assert s.current_strategy == ""
        assert s.timestamp is not None
        assert s.metadata == {}

    def test_create_with_values(self):
        s = CognitiveState(
            health=85.5,
            confidence=72.0,
            focus="availability",
            risk=15.3,
            autonomy_level=4,
            learning_objective="reduce p99 latency",
            current_strategy="scale out workers",
        )
        assert s.health == 85.5
        assert s.confidence == 72.0
        assert s.focus == "availability"
        assert s.risk == 15.3
        assert s.autonomy_level == 4
        assert s.learning_objective == "reduce p99 latency"
        assert s.current_strategy == "scale out workers"

    def test_create_clamp_health(self):
        s = CognitiveState(health=150.0)
        assert s.health == 100.0
        s2 = CognitiveState(health=-10.0)
        assert s2.health == 0.0

    def test_create_clamp_confidence(self):
        s = CognitiveState(confidence=200.0)
        assert s.confidence == 100.0
        s2 = CognitiveState(confidence=-1.0)
        assert s2.confidence == 0.0

    def test_create_clamp_risk(self):
        s = CognitiveState(risk=200.0)
        assert s.risk == 100.0
        s2 = CognitiveState(risk=-10.0)
        assert s2.risk == 0.0

    def test_create_clamp_autonomy(self):
        s = CognitiveState(autonomy_level=10)
        assert s.autonomy_level == 5
        s2 = CognitiveState(autonomy_level=-1)
        assert s2.autonomy_level == 0

    def test_create_invalid_focus_falls_back(self):
        s = CognitiveState(focus="invalid_focus_value")
        assert s.focus == "balanced"

    def test_create_valid_focus_allows(self):
        for focus in ALLOWED_FOCUS_VALUES:
            s = CognitiveState(focus=focus)
            assert s.focus == focus

    def test_to_dict_includes_all_fields(self):
        s = CognitiveState(
            health=80.0, confidence=70.0, focus="latency",
            risk=10.0, autonomy_level=3,
        )
        d = s.to_dict()
        assert d["health"] == 80.0
        assert d["confidence"] == 70.0
        assert d["focus"] == "latency"
        assert d["risk"] == 10.0
        assert d["autonomy_level"] == 3

    def test_from_dict_roundtrip(self):
        s = CognitiveState(
            health=75.0, confidence=65.0, focus="cost",
            risk=20.0, autonomy_level=4,
            learning_objective="reduce cost",
            current_strategy="use cheaper models",
        )
        d = s.to_dict()
        s2 = CognitiveState.from_dict(d)
        assert s2.health == s.health
        assert s2.confidence == s.confidence
        assert s2.focus == s.focus
        assert s2.risk == s.risk
        assert s2.autonomy_level == s.autonomy_level
        assert s2.learning_objective == s.learning_objective
        assert s2.current_strategy == s.current_strategy

    def test_create_with_intent_and_goal_ids(self):
        s = CognitiveState(
            current_intent_id="int_001",
            current_goal_id="goal_002",
        )
        assert s.current_intent_id == "int_001"
        assert s.current_goal_id == "goal_002"

    def test_repr(self):
        s = CognitiveState(health=90.0, confidence=85.0, focus="availability")
        r = repr(s)
        assert "CognitiveState" in r
        assert "90.0" in r

    def test_create_default_id_is_uuid_like(self):
        s = CognitiveState()
        assert len(s.id) > 10

    def test_metadata_default_empty_dict(self):
        s = CognitiveState()
        assert s.metadata == {}

    def test_metadata_roundtrip(self):
        s = CognitiveState(metadata={"source": "test", "trigger": "symptom"})
        d = s.to_dict()
        s2 = CognitiveState.from_dict(d)
        assert s2.metadata["source"] == "test"
        assert s2.metadata["trigger"] == "symptom"

    def test_timestamp_override(self):
        dt = datetime(2025, 6, 1, tzinfo=timezone.utc)
        s = CognitiveState(timestamp=dt)
        assert s.timestamp == dt


# ── CognitiveStateManager Tests ───────────────────────────────────


class TestCognitiveStateManager:
    @pytest.fixture
    def manager(self):
        return CognitiveStateManager()

    async def test_get_initial_state_defaults(self, manager):
        state = await manager.get_current_state()
        assert state.health == 100.0
        assert state.confidence == 100.0
        assert state.focus == "balanced"
        assert state.risk == 0.0
        assert state.autonomy_level == 2

    async def test_get_initial_has_id(self, manager):
        state = await manager.get_current_state()
        assert state.id == "cs_initial"

    async def test_update_health(self, manager):
        await manager.update_state({"health": 75.0})
        state = await manager.get_current_state()
        assert state.health == 75.0

    async def test_update_multiple_fields(self, manager):
        await manager.update_state({
            "health": 80.0,
            "confidence": 70.0,
            "focus": "latency",
            "risk": 15.0,
        })
        state = await manager.get_current_state()
        assert state.health == 80.0
        assert state.confidence == 70.0
        assert state.focus == "latency"
        assert state.risk == 15.0

    async def test_update_preserves_unchanged_fields(self, manager):
        await manager.update_state({"health": 50.0, "focus": "cost"})
        state = await manager.get_current_state()
        assert state.health == 50.0
        assert state.focus == "cost"
        # These should remain defaults
        assert state.confidence == 100.0
        assert state.risk == 0.0

    async def test_update_creates_new_id(self, manager):
        s1 = await manager.get_current_state()
        await manager.update_state({"health": 90.0})
        s2 = await manager.get_current_state()
        assert s2.id != s1.id

    async def test_history_records_transitions(self, manager):
        # Initial state = health 100
        # update(90): archives initial (100), current becomes 90
        # update(80): archives 90, current becomes 80
        # update(70): archives 80, current becomes 70
        await manager.update_state({"health": 90.0})
        await manager.update_state({"health": 80.0})
        await manager.update_state({"health": 70.0})

        history = await manager.get_state_history(limit=10)
        assert len(history) == 3
        # Newest first (reversed): 80 -> 90 -> 100
        assert history[0].health == 80.0, f"got {history[0].health}"
        assert history[1].health == 90.0, f"got {history[1].health}"
        assert history[2].health == 100.0, f"got {history[2].health}"

    async def test_history_limit(self, manager):
        for i in range(20):
            await manager.update_state({"health": float(100 - i)})

        history = await manager.get_state_history(limit=5)
        assert len(history) == 5

    async def test_get_state_count(self, manager):
        assert await manager.get_state_count() == 0
        await manager.update_state({"health": 90.0})
        assert await manager.get_state_count() == 1
        await manager.update_state({"health": 80.0})
        assert await manager.get_state_count() == 2

    async def test_update_retains_idempotent_current(self, manager):
        s1 = await manager.get_current_state()
        await manager.update_state({})
        s2 = await manager.get_current_state()
        # Even with empty updates, a new state is created (timestamp changes)
        assert s2.id != s1.id
        assert s2.health == s1.health

    async def test_update_with_clamping(self, manager):
        await manager.update_state({"health": 200})
        state = await manager.get_current_state()
        assert state.health == 100.0

    async def test_state_history_order_newest_first(self, manager):
        # Initial: balanced
        # update(availability): archives balanced, current=availability
        # update(latency): archives availability, current=latency
        await manager.update_state({"focus": "availability"})
        await manager.update_state({"focus": "latency"})
        history = await manager.get_state_history(limit=10)
        # Reversed (newest archived first): availability -> balanced
        assert history[0].focus == "availability"
        assert history[1].focus == "balanced"
        # Current state = latency
        current = await manager.get_current_state()
        assert current.focus == "latency"
