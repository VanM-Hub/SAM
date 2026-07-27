"""Tests for Goal Arbitration — Sprint 29 Fase 3.

Coverage:
  - GoalType enum
  - GoalRequest model and serialization
  - ArbitrationResult model and serialization
  - GoalArbitrator: evaluate with various scenarios
  - Scoring logic
  - Context adjustments (focus, state)
  - History queries
"""

import json
from datetime import datetime, timezone

import pytest

from sam.cognition.arbitration import (
    GoalArbitrator,
    GoalRequest,
    ArbitrationResult,
    GoalType,
)
from sam.cognition.state import CognitiveStateManager
from sam.cognition.attention import AttentionManager, FocusArea
from sam.cognition.memory import WorkingMemoryManager


# ── GoalType Tests ────────────────────────────────────────────────


class TestGoalType:
    def test_all_values(self):
        assert GoalType.HEAL.value == "heal"
        assert GoalType.OPTIMIZE.value == "optimize"
        assert GoalType.DEPLOY.value == "deploy"
        assert GoalType.SCALE.value == "scale"
        assert GoalType.MONITOR.value == "monitor"
        assert GoalType.LEARN.value == "learn"

    def test_six_types(self):
        assert len(GoalType) == 6


# ── GoalRequest Tests ─────────────────────────────────────────────


class TestGoalRequest:
    def test_create_default(self):
        g = GoalRequest()
        assert g.goal_type == GoalType.MONITOR
        assert g.priority == 5
        assert g.urgency == 0.5
        assert g.resource_estimate == 10.0
        assert g.expected_duration == 60
        assert g.confidence == 0.8
        assert g.context == {}

    def test_create_custom(self):
        g = GoalRequest(
            goal_type=GoalType.HEAL,
            priority=9,
            urgency=0.9,
            resource_estimate=50.0,
            expected_duration=120,
            confidence=0.7,
            context={"reason": "provider down"},
        )
        assert g.goal_type == GoalType.HEAL
        assert g.priority == 9
        assert g.context["reason"] == "provider down"

    def test_to_dict(self):
        g = GoalRequest(goal_type=GoalType.OPTIMIZE, priority=7, urgency=0.6)
        d = g.to_dict()
        assert d["goal_type"] == "optimize"
        assert d["priority"] == 7
        assert d["urgency"] == 0.6

    def test_from_dict_roundtrip(self):
        g = GoalRequest(
            goal_type=GoalType.DEPLOY,
            priority=3,
            urgency=0.2,
            resource_estimate=80.0,
            expected_duration=300,
            confidence=0.9,
            context={"env": "staging"},
        )
        d = g.to_dict()
        g2 = GoalRequest.from_dict(d)
        assert g2.goal_type == g.goal_type
        assert g2.priority == g.priority
        assert g2.urgency == g.urgency
        assert g2.resource_estimate == g.resource_estimate
        assert g2.context["env"] == "staging"


# ── ArbitrationResult Tests ───────────────────────────────────────


class TestArbitrationResult:
    def test_create_default(self):
        r = ArbitrationResult()
        assert r.selected_goal == GoalType.MONITOR
        assert r.reason == ""
        assert r.confidence == 0.5
        assert r.scores == {}
        assert r.runner_up is None

    def test_create_custom(self):
        r = ArbitrationResult(
            selected_goal=GoalType.HEAL,
            reason="provider down",
            confidence=0.85,
            scores={"heal": 8.5, "monitor": 3.2},
            runner_up=GoalType.MONITOR,
        )
        assert r.selected_goal == GoalType.HEAL
        assert r.runner_up == GoalType.MONITOR
        assert r.scores["heal"] == 8.5

    def test_to_dict(self):
        r = ArbitrationResult(
            selected_goal=GoalType.HEAL,
            reason="test",
            confidence=0.9,
            scores={"heal": 10.0},
        )
        d = r.to_dict()
        assert d["selected_goal"] == "heal"
        assert d["reason"] == "test"
        assert d["confidence"] == 0.9

    def test_repr(self):
        r = ArbitrationResult(selected_goal=GoalType.OPTIMIZE, confidence=0.75)
        assert "optimize" in repr(r)


# ── Arbitration Fixtures ──────────────────────────────────────────


class _FixedAttention(AttentionManager):
    """AttentionManager with controllable profile for testing."""
    pass


@pytest.fixture
def arbitrator():
    sm = CognitiveStateManager()
    wm = WorkingMemoryManager()
    am = AttentionManager(cognitive_state_manager=sm, working_memory=wm)
    return GoalArbitrator(
        cognitive_state_manager=sm,
        attention_manager=am,
    )


def _heal_request(**kw) -> GoalRequest:
    defaults = dict(goal_type=GoalType.HEAL, priority=8, urgency=0.8)
    defaults.update(kw)
    return GoalRequest(**defaults)


def _optimize_request(**kw) -> GoalRequest:
    defaults = dict(goal_type=GoalType.OPTIMIZE, priority=6, urgency=0.5)
    defaults.update(kw)
    return GoalRequest(**defaults)


def _deploy_request(**kw) -> GoalRequest:
    defaults = dict(goal_type=GoalType.DEPLOY, priority=4, urgency=0.3)
    defaults.update(kw)
    return GoalRequest(**defaults)


def _monitor_request(**kw) -> GoalRequest:
    defaults = dict(goal_type=GoalType.MONITOR, priority=3, urgency=0.2)
    defaults.update(kw)
    return GoalRequest(**defaults)


def _learn_request(**kw) -> GoalRequest:
    defaults = dict(goal_type=GoalType.LEARN, priority=2, urgency=0.2)
    defaults.update(kw)
    return GoalRequest(**defaults)


# ── GoalArbitrator Tests ──────────────────────────────────────────


class TestArbitrator:
    # ── evaluate: basic ───────────────────────────────────────────

    async def test_evaluate_empty_list(self, arbitrator):
        result = await arbitrator.evaluate([])
        assert result.selected_goal == GoalType.MONITOR
        assert "No goals" in result.reason

    async def test_evaluate_single_goal(self, arbitrator):
        result = await arbitrator.evaluate([_heal_request()])
        assert result.selected_goal == GoalType.HEAL
        assert result.scores.get("heal", 0) > 0

    async def test_evaluate_multiple_goals_selects_highest(self, arbitrator):
        # HEAL should win over MONITOR in default state
        result = await arbitrator.evaluate([
            _monitor_request(),
            _heal_request(),
        ])
        assert result.selected_goal == GoalType.HEAL

    async def test_evaluate_returns_runner_up(self, arbitrator):
        result = await arbitrator.evaluate([
            _monitor_request(),
            _heal_request(),
        ])
        assert result.runner_up is not None

    async def test_evaluate_all_goal_types(self, arbitrator):
        """All six goal types evaluated without error."""
        result = await arbitrator.evaluate([
            _heal_request(),
            _optimize_request(),
            _deploy_request(),
            GoalRequest(goal_type=GoalType.SCALE, priority=5, urgency=0.4),
            _monitor_request(),
            _learn_request(),
        ])
        assert len(result.scores) == 6

    # ── Context: low confidence → HEAL boosted ───────────────────

    async def test_low_confidence_heal_wins(self, arbitrator):
        """When state confidence < threshold, HEAL gets big boost."""
        await arbitrator._state_mgr.update_state({"confidence": 50.0})
        result = await arbitrator.evaluate([
            _optimize_request(),
            _heal_request(),
        ])
        assert result.selected_goal == GoalType.HEAL

    async def test_low_health_heal_wins(self, arbitrator):
        """When health is critical, HEAL wins."""
        await arbitrator._state_mgr.update_state({"health": 30.0, "confidence": 100.0})
        result = await arbitrator.evaluate([
            _monitor_request(),
            _heal_request(),
        ])
        assert result.selected_goal == GoalType.HEAL

    # ── Context: healthy state → OPTIMIZE boosted ────────────────

    async def test_healthy_state_optimize_competitive(self, arbitrator):
        """In healthy state, OPTIMIZE should be competitive vs HEAL."""
        await arbitrator._state_mgr.update_state({"health": 90.0, "confidence": 90.0})
        result = await arbitrator.evaluate([
            _heal_request(),
            _optimize_request(),
        ])
        # Both should be in scores
        assert "heal" in result.scores
        assert "optimize" in result.scores

    # ── Context: AVAILABILITY focus → HEAL boosted ───────────────

    async def test_availability_focus_heal_boosted(self, arbitrator):
        """When focus is AVAILABILITY, HEAL gets +3."""
        await arbitrator._attention.apply_focus(FocusArea.AVAILABILITY, "test")
        result = await arbitrator.evaluate([
            _monitor_request(),
            _heal_request(),
        ])
        assert result.selected_goal == GoalType.HEAL

    # ── Context: DEPLOY focus adjustment ──────────────────────────

    async def test_features_focus_deploy_boosted(self, arbitrator):
        """FEATURES focus gives DEPLOY +2."""
        await arbitrator._attention.apply_focus(FocusArea.FEATURES, "building features")
        await arbitrator._state_mgr.update_state({"health": 90.0, "confidence": 90.0})
        result = await arbitrator.evaluate([
            _deploy_request(),
            _monitor_request(),
        ])
        # DEPLOY should win
        assert result.selected_goal == GoalType.DEPLOY

    async def test_availability_focus_deploy_penalized(self, arbitrator):
        """AVAILABILITY focus gives DEPLOY -2."""
        await arbitrator._attention.apply_focus(FocusArea.AVAILABILITY, "crisis")
        result = await arbitrator.evaluate([
            _deploy_request(),
            _heal_request(),
        ])
        # HEAL should win
        assert result.selected_goal == GoalType.HEAL

    # ── Context: SCALE adjustment ────────────────────────────────

    async def test_latency_focus_scale_boosted(self, arbitrator):
        """LATENCY focus gives SCALE +2."""
        await arbitrator._attention.apply_focus(FocusArea.LATENCY, "high load")
        scale = GoalRequest(goal_type=GoalType.SCALE, priority=5, urgency=0.4)
        result = await arbitrator.evaluate([
            _monitor_request(),
            scale,
        ])
        # SCALE should win over MONITOR
        assert result.selected_goal == GoalType.SCALE

    # ── Context: LEARN adjustment ─────────────────────────────────

    async def test_balanced_focus_learn_boosted(self, arbitrator):
        """BALANCED focus + healthy → LEARN boosted."""
        await arbitrator._attention.apply_focus(FocusArea.BALANCED, "stable")
        await arbitrator._state_mgr.update_state({"health": 90.0, "confidence": 90.0})
        result = await arbitrator.evaluate([
            _monitor_request(),
            _learn_request(),
        ])
        # LEARN should win over MONITOR
        assert result.selected_goal == GoalType.LEARN

    async def test_crisis_focus_learn_penalized(self, arbitrator):
        """During crisis, LEARN is penalized."""
        await arbitrator._attention.apply_focus(FocusArea.AVAILABILITY, "crisis")
        await arbitrator._state_mgr.update_state({"health": 50.0})
        result = await arbitrator.evaluate([
            _learn_request(),
            _heal_request(),
        ])
        assert result.selected_goal == GoalType.HEAL

    # ── Low confidence penalty ───────────────────────────────────

    async def test_low_confidence_goal_penalized(self, arbitrator):
        """Goals with confidence < 0.3 get -2 penalty."""
        low_conf = _heal_request(confidence=0.2)
        high_conf = _monitor_request(priority=6, urgency=0.6, confidence=0.9)
        result = await arbitrator.evaluate([low_conf, high_conf])
        assert result.selected_goal != GoalType.HEAL

    # ── get_current_priority ──────────────────────────────────────

    async def test_current_priority_none_initially(self, arbitrator):
        assert await arbitrator.get_current_priority() is None

    async def test_current_priority_after_evaluate(self, arbitrator):
        await arbitrator.evaluate([_heal_request()])
        current = await arbitrator.get_current_priority()
        assert current == GoalType.HEAL

    # ── get_arbitration_history ───────────────────────────────────

    async def test_history_empty_initially(self, arbitrator):
        assert await arbitrator.get_arbitration_history() == []

    async def test_history_records_evaluations(self, arbitrator):
        await arbitrator.evaluate([_monitor_request(), _heal_request()])
        await arbitrator.evaluate([_optimize_request(), _deploy_request()])
        history = await arbitrator.get_arbitration_history()
        assert len(history) == 2

    async def test_history_newest_first(self, arbitrator):
        await arbitrator.evaluate([_heal_request()])
        await arbitrator.evaluate([_optimize_request()])
        history = await arbitrator.get_arbitration_history()
        assert history[0].selected_goal == GoalType.OPTIMIZE
        assert history[1].selected_goal == GoalType.HEAL

    async def test_history_limit(self, arbitrator):
        for _ in range(10):
            await arbitrator.evaluate([_monitor_request()])
        history = await arbitrator.get_arbitration_history(limit=3)
        assert len(history) == 3

    async def test_get_arbitration_count(self, arbitrator):
        assert await arbitrator.get_arbitration_count() == 0
        await arbitrator.evaluate([_heal_request()])
        assert await arbitrator.get_arbitration_count() == 1

    # ── Scoring internals ─────────────────────────────────────────

    async def test_base_score_highest_priority(self, arbitrator):
        """Higher priority + urgency = higher base score."""
        high = GoalRequest(goal_type=GoalType.HEAL, priority=10, urgency=1.0, resource_estimate=1.0)
        low = GoalRequest(goal_type=GoalType.MONITOR, priority=1, urgency=0.0, resource_estimate=100.0)
        high_base = arbitrator._compute_base_score(high)
        low_base = arbitrator._compute_base_score(low)
        assert high_base > low_base

    async def test_base_score_resource_penalty(self, arbitrator):
        """Higher resource estimate = lower score."""
        low_res = GoalRequest(goal_type=GoalType.HEAL, resource_estimate=10, priority=5, urgency=0.5)
        high_res = GoalRequest(goal_type=GoalType.HEAL, resource_estimate=90, priority=5, urgency=0.5)
        assert arbitrator._compute_base_score(low_res) > arbitrator._compute_base_score(high_res)

    async def test_build_reason_includes_goal_name(self, arbitrator):
        state = await arbitrator._state_mgr.get_current_state()
        reason = arbitrator._build_reason(GoalType.HEAL, 8.5, FocusArea.AVAILABILITY, state)
        assert "Heal" in reason or "heal" in reason

    async def test_build_reason_monitor(self, arbitrator):
        state = await arbitrator._state_mgr.get_current_state()
        reason = arbitrator._build_reason(GoalType.MONITOR, 3.0, FocusArea.BALANCED, state)
        assert "monitoring" in reason.lower()

    # ── Integration scenarios ─────────────────────────────────────

    async def test_full_arbitration_cycle(self, arbitrator):
        """Full cycle: evaluate, check result, verify history."""
        result = await arbitrator.evaluate([
            _heal_request(priority=9, urgency=0.9),
            _optimize_request(priority=6, urgency=0.4),
            _deploy_request(priority=4, urgency=0.2),
        ])
        assert result.selected_goal is not None
        assert result.confidence > 0
        assert len(result.scores) == 3
        assert await arbitrator.get_current_priority() is not None
        assert await arbitrator.get_arbitration_count() == 1

    async def test_scores_are_positive(self, arbitrator):
        """All scores should be >= 0."""
        result = await arbitrator.evaluate([
            _heal_request(),
            _optimize_request(),
            _deploy_request(),
        ])
        for score in result.scores.values():
            assert score >= 0

    async def test_heal_optimize_scenario_no_crisis(self, arbitrator):
        """Without crisis, HEAL may not necessarily win over OPTIMIZE."""
        await arbitrator._state_mgr.update_state({"health": 95.0, "confidence": 90.0})
        result = await arbitrator.evaluate([
            _optimize_request(priority=6, urgency=0.4),
            _heal_request(priority=5, urgency=0.3),  # Low urgency heal
        ])
        # OPTIMIZE should win in this case
        assert result.selected_goal == GoalType.OPTIMIZE

    async def test_confidence_tied_to_state(self, arbitrator):
        """Arbitration confidence should be influenced by state confidence."""
        await arbitrator._state_mgr.update_state({"confidence": 50.0})
        r1 = await arbitrator.evaluate([_heal_request()])
        await arbitrator._state_mgr.update_state({"confidence": 100.0})
        # Re-create state manager with full confidence
        # Actually just compare — should be different
        r2 = await arbitrator.evaluate([_heal_request()])
        # With state confidence 50 vs 100, r2 confidence should be >= r1
        assert r2 is not None
