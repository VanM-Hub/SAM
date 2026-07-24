"""
Sprint 24 – Fase 3 Tests: Predictive Self-Healing & Graceful Degradation

Covers:
  1. HealingStrategy enum and models           (tests 1-4)
  2. HealingManager — registration             (tests 5-8)
  3. HealingManager — pattern detection        (tests 9-13)
  4. HealingManager — execution                (tests 14-17)
  5. DegradationLevel enum                     (tests 18-20)
  6. DegradationManager — degrade/upgrade      (tests 21-25)
  7. DegradationManager — recommendation       (tests 26-30)
  8. Edge cases & integration                  (tests 31-34)
"""

import json
import os
import tempfile
import pytest
from datetime import datetime

from sam.cognitive.healing import (
    HealingStrategy,
    HealingAction,
    HealingResult,
    HealingManager,
    PATTERN_PROVIDER_TIMEOUT,
    PATTERN_ERROR_SPIKE,
)
from sam.cognitive.degradation import (
    DegradationLevel,
    DegradationRecord,
    DegradationManager,
)
from sam.persistence.database import Database


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except PermissionError:
            pass


@pytest.fixture
async def db(db_path):
    database = Database(db_path)
    await database.initialize()
    yield database


# ════════════════════════════════════════════════════════════════════
# 1. Healing Model
# ════════════════════════════════════════════════════════════════════


class TestHealingModel:
    """HealingStrategy, HealingAction, HealingResult models."""

    def test_healing_strategy_values(self):
        """Test 1: All four strategies exist."""
        assert HealingStrategy.PREVENT.value == "prevent"
        assert HealingStrategy.REPAIR.value == "repair"
        assert HealingStrategy.VERIFY.value == "verify"
        assert HealingStrategy.LEARN.value == "learn"

    def test_healing_action_defaults(self):
        """Test 2: Minimal healing action gets sensible defaults."""
        action = HealingAction(trigger="pattern.provider_timeout")
        assert action.id is not None
        assert len(action.id) == 12
        assert action.trigger == "pattern.provider_timeout"
        assert action.strategy == HealingStrategy.REPAIR
        assert action.cooldown == 300
        assert action.precondition is None
        assert action.success_count == 0
        assert action.failure_count == 0
        assert action.last_run_at is None

    def test_healing_action_is_ready(self):
        """Test 3: is_ready returns True when never run, False when on cooldown."""
        action = HealingAction(trigger="t1", cooldown=3600)
        assert action.is_ready() is True

        action.record_run(success=True)
        assert action.is_ready() is False  # 3600s cooldown

        action.last_run_at = None
        assert action.is_ready() is True

    def test_healing_action_record_run(self):
        """Test 4: record_run updates counters and timestamp."""
        action = HealingAction(trigger="t1")
        assert action.success_count == 0
        assert action.failure_count == 0
        assert action.last_run_at is None

        action.record_run(success=True)
        assert action.success_count == 1
        assert action.last_run_at is not None

        action.record_run(success=False)
        assert action.success_count == 1
        assert action.failure_count == 1

    def test_healing_result_model(self):
        """Test 5: HealingResult model."""
        result = HealingResult(
            action_id="a123",
            success=True,
            message="All good",
            duration_ms=42,
            details={"trigger": "t1"},
        )
        assert result.action_id == "a123"
        assert result.success is True
        assert result.details["trigger"] == "t1"


# ════════════════════════════════════════════════════════════════════
# 2. HealingManager — Registration
# ════════════════════════════════════════════════════════════════════

class TestHealingRegistration:
    """Registering patterns and actions."""

    async def test_register_and_get_action(self):
        """Test 6: Register an action then retrieve by trigger."""
        mgr = HealingManager()
        action = HealingAction(trigger=PATTERN_PROVIDER_TIMEOUT, strategy=HealingStrategy.PREVENT)
        await mgr.register_pattern(PATTERN_PROVIDER_TIMEOUT, action)

        actions = await mgr.get_actions_by_trigger(PATTERN_PROVIDER_TIMEOUT)
        assert len(actions) == 1
        assert actions[0].id == action.id
        assert actions[0].strategy == HealingStrategy.PREVENT

    async def test_register_overwrites(self):
        """Test 7: Re-registering same trigger overwrites existing action."""
        mgr = HealingManager()

        a1 = HealingAction(trigger="t1", strategy=HealingStrategy.VERIFY)
        await mgr.register_pattern("t1", a1)

        a2 = HealingAction(trigger="t1", strategy=HealingStrategy.REPAIR)
        await mgr.register_pattern("t1", a2)

        actions = await mgr.get_actions_by_trigger("t1")
        assert len(actions) == 1
        assert actions[0].strategy == HealingStrategy.REPAIR

    async def test_unregister(self):
        """Test 8: Unregister removes the action."""
        mgr = HealingManager()
        await mgr.register_pattern("t1", HealingAction(trigger="t1"))
        assert len(await mgr.get_actions_by_trigger("t1")) == 1

        await mgr.unregister_pattern("t1")
        assert len(await mgr.get_actions_by_trigger("t1")) == 0

    async def test_register_db_persists(self, db):
        """Test 9: Actions registered with DB survive manager recreation."""
        mgr1 = HealingManager(db)
        act = HealingAction(trigger=PATTERN_ERROR_SPIKE, strategy=HealingStrategy.LEARN)
        await mgr1.register_pattern(PATTERN_ERROR_SPIKE, act)

        mgr2 = HealingManager(db)
        actions = await mgr2.get_actions_by_trigger(PATTERN_ERROR_SPIKE)
        assert len(actions) == 1
        assert actions[0].strategy == HealingStrategy.LEARN

    async def test_get_healing_history(self):
        """Test 10: get_healing_history returns sorted actions."""
        mgr = HealingManager()
        a1 = HealingAction(trigger="t1")
        a2 = HealingAction(trigger="t2")
        await mgr.register_pattern("t1", a1)
        await mgr.register_pattern("t2", a2)

        history = await mgr.get_healing_history()
        assert len(history) == 2


# ════════════════════════════════════════════════════════════════════
# 3. HealingManager — Pattern Detection
# ════════════════════════════════════════════════════════════════════

class TestPatternDetection:
    """Detecting patterns from evidence."""

    async def test_detect_direct_match(self):
        """Test 11: Exact pattern key in evidence matches registered action."""
        mgr = HealingManager()
        await mgr.register_pattern(
            PATTERN_PROVIDER_TIMEOUT,
            HealingAction(trigger=PATTERN_PROVIDER_TIMEOUT, strategy=HealingStrategy.PREVENT),
        )

        evidence = [{"pattern": PATTERN_PROVIDER_TIMEOUT, "value": 0.95}]
        matched = await mgr.detect_patterns(evidence)
        assert len(matched) == 1
        assert matched[0].trigger == PATTERN_PROVIDER_TIMEOUT

    async def test_detect_evidence_prefix(self):
        """Test 12: Evidence with 'type' field matches registered pattern with evidence. prefix."""
        mgr = HealingManager()
        await mgr.register_pattern(
            "evidence.timeout",
            HealingAction(trigger="evidence.timeout"),
        )

        evidence = [{"type": "timeout", "value": 1}]
        matched = await mgr.detect_patterns(evidence)
        assert len(matched) == 1

    async def test_detect_pattern_prefix(self):
        """Test 13: Evidence with 'type' matches pattern.*type*."""
        mgr = HealingManager()
        await mgr.register_pattern(
            "pattern.memory_leak",
            HealingAction(trigger="pattern.memory_leak"),
        )

        evidence = [{"type": "memory_leak", "severity": "high"}]
        matched = await mgr.detect_patterns(evidence)
        assert len(matched) == 1

    async def test_detect_no_match(self):
        """Test 14: Evidence without pattern/type returns no matches."""
        mgr = HealingManager()
        await mgr.register_pattern("t1", HealingAction(trigger="t1"))

        evidence = [{"unknown": "data"}]
        matched = await mgr.detect_patterns(evidence)
        assert len(matched) == 0

    async def test_detect_deduplicates(self):
        """Test 15: Same action matched via multiple patterns only returned once."""
        mgr = HealingManager()
        action = HealingAction(trigger="t1")
        await mgr.register_pattern("t1", action)

        evidence = [{"pattern": "t1"}, {"type": "t1"}]
        matched = await mgr.detect_patterns(evidence)
        assert len(matched) == 1  # deduplicated


# ════════════════════════════════════════════════════════════════════
# 4. HealingManager — Execution
# ════════════════════════════════════════════════════════════════════

class TestHealingExecution:
    """Executing healing actions."""

    async def test_execute_success(self):
        """Test 16: Successful healing returns result with success=True."""
        mgr = HealingManager()
        action = HealingAction(
            trigger="t1",
            strategy=HealingStrategy.VERIFY,
            action_graph=[{"name": "check_disk", "command": "df"}],
        )
        result = await mgr.execute_healing(action)
        assert result.success is True
        assert result.action_id == action.id
        assert "completed" in result.message

    async def test_execute_failure(self):
        """Test 17: Healing with failing steps returns success=False."""
        mgr = HealingManager()
        action = HealingAction(
            trigger="t2",
            action_graph=[{"name": "bad_step", "fail": True}],
        )
        result = await mgr.execute_healing(action)
        assert result.success is False
        assert "fail" in result.message.lower() or "fail" in result.details.get("strategy", "")

    async def test_execute_success_updates_counters(self):
        """Test 18: Successful execution increments success_count."""
        mgr = HealingManager()
        action = HealingAction(trigger="t1", strategy=HealingStrategy.PREVENT)
        assert action.success_count == 0

        await mgr.execute_healing(action)
        assert action.success_count == 1
        assert action.last_run_at is not None

    async def test_execute_failure_updates_counters(self):
        """Test 19: Failed execution increments failure_count."""
        mgr = HealingManager()
        action = HealingAction(
            trigger="t2",
            action_graph=[{"name": "fail", "fail": True}],
        )
        assert action.failure_count == 0

        await mgr.execute_healing(action)
        assert action.failure_count == 1

    async def test_execute_updates_db(self, db):
        """Test 20: Execution stats persist after run (DB-backed)."""
        mgr = HealingManager(db)
        action = HealingAction(trigger="t1", strategy=HealingStrategy.REPAIR)
        await mgr.register_pattern("t1", action)

        await mgr.execute_healing(action)

        # Reload from DB
        mgr2 = HealingManager(db)
        actions = await mgr2.get_actions_by_trigger("t1")
        assert len(actions) == 1
        assert actions[0].success_count == 1


# ════════════════════════════════════════════════════════════════════
# 5. DegradationLevel enum
# ════════════════════════════════════════════════════════════════════

class TestDegradationLevelEnum:
    """Degradation level values and conversions."""

    def test_enum_values(self):
        """Test 21: All five levels exist."""
        assert DegradationLevel.OBSERVE_ONLY.value == "observe_only"
        assert DegradationLevel.RECOMMENDATION_ONLY.value == "recommendation_only"
        assert DegradationLevel.ASSISTED.value == "assisted"
        assert DegradationLevel.SUPERVISED.value == "supervised"
        assert DegradationLevel.AUTONOMOUS.value == "autonomous"

    def test_numeric_values(self):
        """Test 22: Numeric values 0–4."""
        assert DegradationLevel.OBSERVE_ONLY.numeric == 0
        assert DegradationLevel.RECOMMENDATION_ONLY.numeric == 1
        assert DegradationLevel.ASSISTED.numeric == 2
        assert DegradationLevel.SUPERVISED.numeric == 3
        assert DegradationLevel.AUTONOMOUS.numeric == 4

    def test_from_numeric(self):
        """Test 23: from_numeric conversion."""
        assert DegradationLevel.from_numeric(0) == DegradationLevel.OBSERVE_ONLY
        assert DegradationLevel.from_numeric(4) == DegradationLevel.AUTONOMOUS

    def test_from_numeric_invalid(self):
        """Test 24: Invalid number raises."""
        with pytest.raises(ValueError):
            DegradationLevel.from_numeric(99)

    def test_to_autonomy_level(self):
        """Test 25: Mapping to AutonomyLevel."""
        assert DegradationLevel.AUTONOMOUS.to_autonomy_level() is not None


# ════════════════════════════════════════════════════════════════════
# 6. DegradationManager — degrade/upgrade
# ════════════════════════════════════════════════════════════════════

class TestDegradationTransitions:
    """Degrade and upgrade operations."""

    async def test_initial_level(self):
        """Test 26: Default initial level is AUTONOMOUS."""
        mgr = DegradationManager()
        level = await mgr.get_current_level()
        assert level == DegradationLevel.AUTONOMOUS

    async def test_degrade_once(self):
        """Test 27: degrade() drops one level."""
        mgr = DegradationManager()
        new = await mgr.degrade()
        assert new == DegradationLevel.SUPERVISED
        assert await mgr.get_current_level() == DegradationLevel.SUPERVISED

    async def test_degrade_full_chain(self):
        """Test 28: Full degradation chain 4→0."""
        mgr = DegradationManager()
        assert await mgr.degrade() == DegradationLevel.SUPERVISED   # 3
        assert await mgr.degrade() == DegradationLevel.ASSISTED     # 2
        assert await mgr.degrade() == DegradationLevel.RECOMMENDATION_ONLY  # 1
        assert await mgr.degrade() == DegradationLevel.OBSERVE_ONLY  # 0

    async def test_degrade_below_minimum(self):
        """Test 29: Degrade at minimum level stays at OBSERVE_ONLY."""
        mgr = DegradationManager()
        # Force to minimum
        for _ in range(4):
            await mgr.degrade()
        assert await mgr.get_current_level() == DegradationLevel.OBSERVE_ONLY

        # Trying to degrade further stays at 0
        result = await mgr.degrade()
        assert result == DegradationLevel.OBSERVE_ONLY

    async def test_upgrade_once(self):
        """Test 30: upgrade() rises one level."""
        mgr = DegradationManager()
        # First degrade to ASSISTED
        await mgr.degrade()
        await mgr.degrade()
        assert await mgr.get_current_level() == DegradationLevel.ASSISTED

        result = await mgr.upgrade()
        assert result == DegradationLevel.SUPERVISED

    async def test_upgrade_full_chain(self):
        """Test 31: Full upgrade chain 0→4."""
        mgr = DegradationManager()
        # Degrade to 0 first
        for _ in range(4):
            await mgr.degrade()
        assert await mgr.get_current_level() == DegradationLevel.OBSERVE_ONLY

        # Now upgrade
        assert await mgr.upgrade() == DegradationLevel.RECOMMENDATION_ONLY
        assert await mgr.upgrade() == DegradationLevel.ASSISTED
        assert await mgr.upgrade() == DegradationLevel.SUPERVISED
        assert await mgr.upgrade() == DegradationLevel.AUTONOMOUS

    async def test_upgrade_above_maximum(self):
        """Test 32: Upgrade at maximum stays at AUTONOMOUS."""
        mgr = DegradationManager()
        result = await mgr.upgrade()
        assert result == DegradationLevel.AUTONOMOUS

    async def test_set_level(self):
        """Test 33: set_level jumps to any level."""
        mgr = DegradationManager()
        await mgr.set_level(DegradationLevel.OBSERVE_ONLY)
        assert await mgr.get_current_level() == DegradationLevel.OBSERVE_ONLY

        await mgr.set_level(DegradationLevel.AUTONOMOUS)
        assert await mgr.get_current_level() == DegradationLevel.AUTONOMOUS


# ════════════════════════════════════════════════════════════════════
# 7. DegradationManager — Recommendation
# ════════════════════════════════════════════════════════════════════

class TestDegradationRecommendation:
    """Context-based level recommendation."""

    async def test_recommend_healthy(self):
        """Test 34: Healthy system recommends AUTONOMOUS."""
        mgr = DegradationManager()
        context = {
            "error_rate": 0.0,
            "budget_remaining": {
                "reasoning_cycles": 5, "planning_attempts": 3,
                "revision_count": 3, "learning_iterations": 10,
            },
            "health_score": 1.0,
            "consecutive_failures": 0,
        }
        level = await mgr.get_recommended_level(context)
        assert level == DegradationLevel.AUTONOMOUS

    async def test_recommend_high_error_rate(self):
        """Test 35: High error rate (>40%) recommends OBSERVE_ONLY."""
        mgr = DegradationManager()
        level = await mgr.get_recommended_level({"error_rate": 0.5})
        assert level == DegradationLevel.OBSERVE_ONLY

    async def test_recommend_medium_error_rate(self):
        """Test 36: Medium error rate (10-15%) recommends SUPERVISED."""
        mgr = DegradationManager()
        level = await mgr.get_recommended_level({"error_rate": 0.10})
        assert level == DegradationLevel.SUPERVISED

    async def test_recommend_budget_exhausted_three(self):
        """Test 37: Three or more exhausted budgets → RECOMMENDATION_ONLY."""
        mgr = DegradationManager()
        context = {
            "error_rate": 0.0,
            "budget_remaining": {
                "a": 0, "b": 0, "c": 0, "d": 5,
            },
        }
        level = await mgr.get_recommended_level(context)
        assert level == DegradationLevel.RECOMMENDATION_ONLY

    async def test_recommend_budget_exhausted_two(self):
        """Test 38: Two exhausted budgets → ASSISTED."""
        mgr = DegradationManager()
        context = {
            "error_rate": 0.0,
            "budget_remaining": {
                "a": 0, "b": 0, "c": 3, "d": 5,
            },
        }
        level = await mgr.get_recommended_level(context)
        assert level == DegradationLevel.ASSISTED

    async def test_recommend_budget_exhausted_one(self):
        """Test 39: One exhausted budget → SUPERVISED."""
        mgr = DegradationManager()
        context = {
            "error_rate": 0.0,
            "budget_remaining": {
                "a": 0, "b": 3, "c": 3, "d": 5,
            },
        }
        level = await mgr.get_recommended_level(context)
        assert level == DegradationLevel.SUPERVISED

    async def test_recommend_low_health_score(self):
        """Test 40: Health score < 30% degrades two levels."""
        mgr = DegradationManager()
        level = await mgr.get_recommended_level({
            "error_rate": 0.0, "health_score": 0.2,
        })
        assert level == DegradationLevel.ASSISTED

    async def test_recommend_many_consecutive_failures(self):
        """Test 41: >10 consecutive failures → OBSERVE_ONLY."""
        mgr = DegradationManager()
        level = await mgr.get_recommended_level({
            "error_rate": 0.0, "consecutive_failures": 12,
        })
        assert level == DegradationLevel.OBSERVE_ONLY

    async def test_recommend_compound_penalties(self):
        """Test 42: Multiple issues compound (error 0.08 = SUPERVISED at most,
        health 0.5 = SUPERVISED at most, consecutive 3 = SUPERVISED at most).
        Result should be SUPERVISED."""
        mgr = DegradationManager()
        context = {
            "error_rate": 0.08,
            "budget_remaining": {},
            "health_score": 0.5,
            "consecutive_failures": 3,
        }
        level = await mgr.get_recommended_level(context)
        # All three penalties cap at SUPERVISED (3), final = 3
        assert level == DegradationLevel.SUPERVISED


# ════════════════════════════════════════════════════════════════════
# 8. Integration & Edge Cases
# ════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Cross-module and persistence scenarios."""

    async def test_healing_db_persistence(self, db):
        """Test 43: Healing manager with DB persists actions properly."""
        mgr = HealingManager(db)
        action = HealingAction(trigger="t1", strategy=HealingStrategy.VERIFY)
        await mgr.register_pattern("t1", action)

        # Verify in DB directly
        row = await db.fetch_one("SELECT * FROM healing_actions WHERE trigger = ?", ["t1"])
        assert row is not None
        assert row["strategy"] == "verify"

    async def test_degradation_db_persistence(self, db):
        """Test 44: Degradation history persists across managers."""
        mgr1 = DegradationManager(db)
        await mgr1.degrade()
        await mgr1.degrade()

        # New manager loads from DB
        mgr2 = DegradationManager(db)
        level = await mgr2.get_current_level()
        assert level == DegradationLevel.ASSISTED

        history = await mgr2.get_history()
        assert len(history) >= 2

    async def test_degradation_history_records(self):
        """Test 45: History includes previous and new levels."""
        mgr = DegradationManager()
        await mgr.degrade()
        history = await mgr.get_history()
        assert len(history) == 1
        assert history[0].previous_level == DegradationLevel.AUTONOMOUS
        assert history[0].new_level == DegradationLevel.SUPERVISED
        assert "degraded" in history[0].reason.lower()

    async def test_set_level_reason(self):
        """Test 46: set_level records custom reason."""
        mgr = DegradationManager()
        await mgr.set_level(DegradationLevel.OBSERVE_ONLY, reason="Manual override for maintenance")
        history = await mgr.get_history()
        assert len(history) == 1
        assert "Manual override" in history[0].reason
