"""Tests for Attention Manager — Sprint 29 Fase 2.

Coverage:
  - FocusArea enum values
  - AttentionProfile creation, serialization, validation
  - AttentionManager: determine_focus logic (all 6 rules)
  - AttentionManager: apply_focus, get_current_profile, update_weights
  - History queries
  - Integration with CognitiveStateManager + WorkingMemoryManager
"""

import json
from datetime import datetime, timezone

import pytest

from sam.cognition.attention import (
    AttentionManager,
    AttentionProfile,
    FocusArea,
    DEFAULT_WEIGHTS,
    FOCUS_WEIGHT_MAP,
)
from sam.cognition.state import CognitiveStateManager
from sam.cognition.memory import WorkingMemoryManager


# ── FocusArea Tests ───────────────────────────────────────────────


class TestFocusArea:
    def test_enum_values(self):
        assert FocusArea.AVAILABILITY.value == "availability"
        assert FocusArea.LATENCY.value == "latency"
        assert FocusArea.COST.value == "cost"
        assert FocusArea.SECURITY.value == "security"
        assert FocusArea.FEATURES.value == "features"
        assert FocusArea.BALANCED.value == "balanced"

    def test_all_six_values(self):
        assert len(FocusArea) == 6


# ── AttentionProfile Tests ────────────────────────────────────────


class TestAttentionProfile:
    def test_create_default(self):
        p = AttentionProfile()
        assert p.primary_focus == FocusArea.BALANCED
        assert p.secondary_focus is None
        assert p.weights == DEFAULT_WEIGHTS
        assert p.reason == ""
        assert p.confidence == 1.0
        assert p.id.startswith("ap_")

    def test_create_with_focus(self):
        p = AttentionProfile(primary_focus=FocusArea.AVAILABILITY, reason="low confidence")
        assert p.primary_focus == FocusArea.AVAILABILITY
        assert p.reason == "low confidence"

    def test_create_with_secondary(self):
        p = AttentionProfile(
            primary_focus=FocusArea.AVAILABILITY,
            secondary_focus=FocusArea.LATENCY,
        )
        assert p.secondary_focus == FocusArea.LATENCY

    def test_create_with_custom_weights(self):
        w = {"availability": 0.5, "latency": 0.5, "cost": 0.0, "security": 0.0, "features": 0.0}
        p = AttentionProfile(weights=w)
        assert p.weights["availability"] == 0.5

    def test_confidence_clamp(self):
        p = AttentionProfile(confidence=2.0)
        assert p.confidence == 1.0
        p2 = AttentionProfile(confidence=-1.0)
        assert p2.confidence == 0.0

    def test_to_dict_includes_all(self):
        p = AttentionProfile(
            primary_focus=FocusArea.COST,
            secondary_focus=FocusArea.AVAILABILITY,
            reason="cost too high",
            confidence=0.85,
        )
        d = p.to_dict()
        assert d["primary_focus"] == "cost"
        assert d["secondary_focus"] == "availability"
        assert d["reason"] == "cost too high"
        assert d["confidence"] == 0.85

    def test_from_dict_roundtrip(self):
        p = AttentionProfile(
            primary_focus=FocusArea.LATENCY,
            secondary_focus=FocusArea.COST,
            reason="latency spike",
            confidence=0.7,
        )
        d = p.to_dict()
        p2 = AttentionProfile.from_dict(d)
        assert p2.primary_focus == p.primary_focus
        assert p2.secondary_focus == p.secondary_focus
        assert p2.reason == p.reason
        assert p2.confidence == p.confidence

    def test_repr(self):
        p = AttentionProfile(primary_focus=FocusArea.AVAILABILITY, confidence=0.9)
        r = repr(p)
        assert "AttentionProfile" in r
        assert "availability" in r

    def test_timestamp_default(self):
        p = AttentionProfile()
        assert p.timestamp is not None


# ── Attention Manager Tests ───────────────────────────────────────


class _FixedStateManager(CognitiveStateManager):
    """StateManager with controllable initial state."""
    pass


class TestAttentionManager:
    @pytest.fixture
    def am(self):
        sm = CognitiveStateManager()
        wm = WorkingMemoryManager()
        return AttentionManager(
            cognitive_state_manager=sm,
            working_memory=wm,
        )

    # ── determine_focus: rule 1 — low confidence → AVAILABILITY ───

    async def test_determine_low_confidence_availability(self, am):
        focus = await am.determine_focus({"operational_confidence": 50.0})
        assert focus == FocusArea.AVAILABILITY

    async def test_determine_high_confidence_not_availability(self, am):
        # Default state: health=100, confidence=100 → should be BALANCED
        # We need to test without context override to see default behavior
        # With no context and healthy defaults, should be BALANCED
        focus = await am.determine_focus()
        assert focus == FocusArea.BALANCED

    async def test_determine_confidence_at_threshold_not_availability(self, am):
        focus = await am.determine_focus({"operational_confidence": 70.0})
        assert focus != FocusArea.AVAILABILITY  # at threshold = not below

    # ── determine_focus: rule 2 — low health → AVAILABILITY ──────

    async def test_determine_low_health_availability(self, am):
        focus = await am.determine_focus({"health": 30.0, "operational_confidence": 100.0})
        assert focus == FocusArea.AVAILABILITY

    async def test_determine_healthy_not_availability(self, am):
        focus = await am.determine_focus({"health": 80.0, "operational_confidence": 100.0})
        assert focus != FocusArea.AVAILABILITY

    # ── determine_focus: rule 3 — health drop → AVAILABILITY ─────

    async def test_determine_health_drop_availability(self, am):
        # Set a history entry with high health
        await am._state_mgr.update_state({"health": 100.0})
        # Now drop significantly
        await am._state_mgr.update_state({"health": 70.0})  # drop 30
        focus = await am.determine_focus({"operational_confidence": 100.0})
        assert focus == FocusArea.AVAILABILITY

    async def test_determine_small_health_drop_not_availability(self, am):
        await am._state_mgr.update_state({"health": 100.0})
        await am._state_mgr.update_state({"health": 95.0})  # drop 5
        focus = await am.determine_focus({"operational_confidence": 100.0})
        assert focus != FocusArea.AVAILABILITY

    # ── determine_focus: rule 4 — high CPU/memory → LATENCY ─────

    async def test_determine_high_cpu_latency(self, am):
        focus = await am.determine_focus({
            "cpu_usage": 90.0,
            "memory_usage": 30.0,
            "operational_confidence": 100.0,
            "health": 90.0,
            "has_active_failure": False,
        })
        assert focus == FocusArea.LATENCY

    async def test_determine_high_memory_latency(self, am):
        focus = await am.determine_focus({
            "cpu_usage": 30.0,
            "memory_usage": 90.0,
            "operational_confidence": 100.0,
            "health": 90.0,
            "has_active_failure": False,
        })
        assert focus == FocusArea.LATENCY

    async def test_determine_high_cpu_with_failure_not_latency(self, am):
        # If there's a failure, availability takes priority
        focus = await am.determine_focus({
            "cpu_usage": 90.0,
            "memory_usage": 30.0,
            "operational_confidence": 100.0,
            "health": 90.0,
            "has_active_failure": True,
        })
        # With no low confidence/health, would check BALANCED vs LATENCY
        # has_active_failure=True should prevent LATENCY → BALANCED
        assert focus != FocusArea.LATENCY

    async def test_determine_low_cpu_mem_not_latency(self, am):
        focus = await am.determine_focus({
            "cpu_usage": 30.0,
            "memory_usage": 30.0,
            "operational_confidence": 100.0,
            "health": 90.0,
        })
        assert focus != FocusArea.LATENCY

    # ── determine_focus: rule 5 — high cost → COST ──────────────

    async def test_determine_high_cost_focus(self, am):
        focus = await am.determine_focus({
            "operational_cost": 500.0,
            "operational_confidence": 100.0,
            "health": 90.0,
            "cpu_usage": 30.0,
            "memory_usage": 30.0,
        })
        assert focus == FocusArea.COST

    async def test_determine_low_cost_not_cost(self, am):
        focus = await am.determine_focus({
            "operational_cost": 10.0,
            "operational_confidence": 100.0,
            "health": 90.0,
            "cpu_usage": 30.0,
            "memory_usage": 30.0,
        })
        assert focus != FocusArea.COST

    # ── determine_focus: rule 6 — default → BALANCED ────────────

    async def test_determine_default_balanced(self, am):
        focus = await am.determine_focus({
            "operational_confidence": 100.0,
            "health": 90.0,
            "cpu_usage": 30.0,
            "memory_usage": 30.0,
            "operational_cost": 10.0,
        })
        assert focus == FocusArea.BALANCED

    # ── apply_focus ──────────────────────────────────────────────

    async def test_apply_focus_creates_profile(self, am):
        profile = await am.apply_focus(FocusArea.LATENCY, "latency sensitive")
        assert profile.primary_focus == FocusArea.LATENCY
        assert profile.reason == "latency sensitive"
        assert profile.secondary_focus == FocusArea.COST  # suggested secondary

    async def test_apply_focus_updates_current(self, am):
        await am.apply_focus(FocusArea.COST, "expensive")
        current = await am.get_current_profile()
        assert current.primary_focus == FocusArea.COST

    async def test_apply_focus_archives_previous(self, am):
        await am.apply_focus(FocusArea.AVAILABILITY, "first")
        await am.apply_focus(FocusArea.LATENCY, "second")
        history = await am.get_focus_history()
        assert len(history) == 1
        assert history[0].primary_focus == FocusArea.AVAILABILITY

    async def test_apply_focus_updates_cognitive_state(self, am):
        await am.apply_focus(FocusArea.SECURITY, "security breach risk")
        state = await am._state_mgr.get_current_state()
        assert state.focus == "security"

    # ── determine_and_apply ──────────────────────────────────────

    async def test_determine_and_apply_low_confidence(self, am):
        profile = await am.determine_and_apply({"operational_confidence": 40.0})
        assert profile.primary_focus == FocusArea.AVAILABILITY
        assert "40.0" in profile.reason

    async def test_determine_and_apply_healthy_balanced(self, am):
        profile = await am.determine_and_apply({
            "operational_confidence": 100.0,
            "health": 90.0,
            "cpu_usage": 30.0,
            "memory_usage": 30.0,
        })
        assert profile.primary_focus == FocusArea.BALANCED
        assert "Stable" in profile.reason or "balanced" in profile.reason

    # ── get_current_profile ──────────────────────────────────────

    async def test_get_current_profile_initial_default(self, am):
        profile = await am.get_current_profile()
        assert profile is not None
        assert profile.primary_focus == FocusArea.BALANCED

    async def test_get_current_profile_after_apply(self, am):
        await am.apply_focus(FocusArea.LATENCY, "test")
        profile = await am.get_current_profile()
        assert profile.primary_focus == FocusArea.LATENCY

    # ── update_weights ───────────────────────────────────────────

    async def test_update_weights(self, am):
        await am.apply_focus(FocusArea.AVAILABILITY, "test")
        new_weights = {"availability": 0.8, "latency": 0.1, "cost": 0.05, "security": 0.03, "features": 0.02}
        await am.update_weights(new_weights)
        profile = await am.get_current_profile()
        assert abs(profile.weights["availability"] - 0.8) < 0.01
        assert abs(profile.weights["latency"] - 0.1) < 0.01

    async def test_update_weights_normalizes(self, am):
        await am.apply_focus(FocusArea.BALANCED, "test")
        await am.update_weights({"availability": 10, "latency": 10, "cost": 0, "security": 0, "features": 0})
        profile = await am.get_current_profile()
        total = sum(profile.weights.values())
        assert abs(total - 1.0) < 0.01

    # ── get_focus_history ────────────────────────────────────────

    async def test_focus_history_empty_initially(self, am):
        history = await am.get_focus_history()
        assert history == []

    async def test_focus_history_tracks_transitions(self, am):
        await am.apply_focus(FocusArea.AVAILABILITY, "a")
        await am.apply_focus(FocusArea.LATENCY, "b")
        await am.apply_focus(FocusArea.COST, "c")
        history = await am.get_focus_history()
        # 2 archived (first two), newest first: LATENCY then AVAILABILITY
        assert len(history) == 2
        assert history[0].primary_focus == FocusArea.LATENCY
        assert history[1].primary_focus == FocusArea.AVAILABILITY
        current = await am.get_current_profile()
        assert current.primary_focus == FocusArea.COST

    async def test_focus_history_limit(self, am):
        for i in range(10):
            await am.apply_focus(FocusArea.BALANCED, str(i))
        history = await am.get_focus_history(limit=3)
        assert len(history) == 3

    async def test_get_profile_count(self, am):
        assert await am.get_profile_count() == 0
        await am.apply_focus(FocusArea.AVAILABILITY, "x")
        assert await am.get_profile_count() == 0  # current not counted
        await am.apply_focus(FocusArea.LATENCY, "y")
        assert await am.get_profile_count() == 1

    # ── Weights from FOCUS_WEIGHT_MAP ────────────────────────────

    async def test_weights_availability(self, am):
        profile = await am.apply_focus(FocusArea.AVAILABILITY, "test")
        assert profile.weights["availability"] == 0.60

    async def test_weights_latency(self, am):
        profile = await am.apply_focus(FocusArea.LATENCY, "test")
        assert profile.weights["latency"] == 0.50

    async def test_weights_cost(self, am):
        profile = await am.apply_focus(FocusArea.COST, "test")
        assert profile.weights["cost"] == 0.55

    async def test_weights_balanced(self, am):
        profile = await am.apply_focus(FocusArea.BALANCED, "test")
        assert abs(profile.weights["availability"] - 0.25) < 0.01

    # ── Integration: cognitive state reflects focus ──────────────

    async def test_cognitive_state_focus_synced(self, am):
        await am.apply_focus(FocusArea.SECURITY, "security event")
        state = await am._state_mgr.get_current_state()
        assert state.focus == "security"

    async def test_focus_priority_availability_over_cost(self, am):
        """Low confidence + high cost → AVAILABILITY (rule 1 wins)."""
        focus = await am.determine_focus({
            "operational_confidence": 50.0,
            "health": 90.0,
            "operational_cost": 500.0,
            "cpu_usage": 30.0,
            "memory_usage": 30.0,
        })
        assert focus == FocusArea.AVAILABILITY

    async def test_read_metric_from_working_memory(self, am):
        """determine_focus can read cpu_usage from working memory."""
        await am._wm.set("cpu_usage", 95.0)
        await am._wm.set("memory_usage", 92.0)
        focus = await am.determine_focus({
            "operational_confidence": 100.0,
            "health": 90.0,
            "has_active_failure": False,
        })
        assert focus == FocusArea.LATENCY
