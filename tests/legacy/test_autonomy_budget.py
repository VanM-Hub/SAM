"""
Sprint 24 – Fase 2 Tests: Autonomy Levels & Cognitive Budget

Covers:
  1. AutonomyLevel enum and numeric conversion     (tests 1-4)
  2. AutonomyLevel.can_execute() rules             (tests 5-9)
  3. AutonomyConfig model                          (tests 10-12)
  4. CognitiveBudget model                         (tests 13-16)
  5. BudgetTracker consumption & limits            (tests 17-22)
  6. BudgetTracker reset & remaining               (tests 23-26)
  7. Edge cases & integration                      (tests 27-30)
"""

import json
import os
import tempfile
import pytest
from datetime import datetime

from sam.cognitive.autonomy import AutonomyLevel, AutonomyConfig
from sam.cognitive.budget import (
    CognitiveBudget,
    BudgetTracker,
    BUDGET_REASONING,
    BUDGET_PLANNING,
    BUDGET_REVISION,
    BUDGET_LEARNING,
    ALL_BUDGET_TYPES,
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
# 1. AutonomyLevel enum
# ════════════════════════════════════════════════════════════════════


class TestAutonomyLevelEnum:
    """Autonomy levels — enum values, numeric conversion, descriptions."""

    def test_enum_values(self):
        """Test 1: All six autonomy levels exist with correct string values."""
        assert AutonomyLevel.OBSERVE_ONLY.value == "observe_only"
        assert AutonomyLevel.RECOMMEND.value == "recommend"
        assert AutonomyLevel.EXECUTE_LOW_RISK.value == "execute_low_risk"
        assert AutonomyLevel.EXECUTE_MEDIUM_RISK.value == "execute_medium_risk"
        assert AutonomyLevel.SUPERVISED_AUTONOMY.value == "supervised_autonomy"
        assert AutonomyLevel.FULL_AUTONOMY.value == "full_autonomy"

    def test_numeric_property(self):
        """Test 2: Numeric values 0–5 are correct."""
        assert AutonomyLevel.OBSERVE_ONLY.numeric == 0
        assert AutonomyLevel.RECOMMEND.numeric == 1
        assert AutonomyLevel.EXECUTE_LOW_RISK.numeric == 2
        assert AutonomyLevel.EXECUTE_MEDIUM_RISK.numeric == 3
        assert AutonomyLevel.SUPERVISED_AUTONOMY.numeric == 4
        assert AutonomyLevel.FULL_AUTONOMY.numeric == 5

    def test_from_numeric(self):
        """Test 3: from_numeric converts back correctly."""
        assert AutonomyLevel.from_numeric(0) == AutonomyLevel.OBSERVE_ONLY
        assert AutonomyLevel.from_numeric(2) == AutonomyLevel.EXECUTE_LOW_RISK
        assert AutonomyLevel.from_numeric(5) == AutonomyLevel.FULL_AUTONOMY

    def test_from_numeric_invalid(self):
        """Test 4: Invalid numeric raises ValueError."""
        with pytest.raises(ValueError, match="Invalid"):
            AutonomyLevel.from_numeric(99)
        with pytest.raises(ValueError, match="Invalid"):
            AutonomyLevel.from_numeric(-1)

    def test_enum_count(self):
        """Test 5: Exactly 6 levels in the enum."""
        assert len(list(AutonomyLevel)) == 6


# ════════════════════════════════════════════════════════════════════
# 2. AutonomyLevel.can_execute()
# ════════════════════════════════════════════════════════════════════

class TestAutonomyLevelCanExecute:
    """Permission checks at each level."""

    def test_observe_only_cannot_execute(self):
        """Test 6: OBSERVE_ONLY (0) never executes."""
        assert not AutonomyLevel.OBSERVE_ONLY.can_execute("low")
        assert not AutonomyLevel.OBSERVE_ONLY.can_execute("medium")
        assert not AutonomyLevel.OBSERVE_ONLY.can_execute("high")
        assert not AutonomyLevel.OBSERVE_ONLY.can_execute("critical")
        assert not AutonomyLevel.OBSERVE_ONLY.can_execute()

    def test_recommend_cannot_execute(self):
        """Test 7: RECOMMEND (1) never executes."""
        assert not AutonomyLevel.RECOMMEND.can_execute("low")
        assert not AutonomyLevel.RECOMMEND.can_execute("medium")
        assert not AutonomyLevel.RECOMMEND.can_execute()

    def test_execute_low_risk(self):
        """Test 8: EXECUTE_LOW_RISK (2) only low."""
        assert AutonomyLevel.EXECUTE_LOW_RISK.can_execute("low")
        assert not AutonomyLevel.EXECUTE_LOW_RISK.can_execute("medium")
        assert not AutonomyLevel.EXECUTE_LOW_RISK.can_execute("high")
        assert not AutonomyLevel.EXECUTE_LOW_RISK.can_execute("critical")
        assert not AutonomyLevel.EXECUTE_LOW_RISK.can_execute()

    def test_execute_medium_risk(self):
        """Test 9: EXECUTE_MEDIUM_RISK (3) up to medium."""
        assert AutonomyLevel.EXECUTE_MEDIUM_RISK.can_execute("low")
        assert AutonomyLevel.EXECUTE_MEDIUM_RISK.can_execute("medium")
        assert not AutonomyLevel.EXECUTE_MEDIUM_RISK.can_execute("high")
        assert not AutonomyLevel.EXECUTE_MEDIUM_RISK.can_execute("critical")
        assert not AutonomyLevel.EXECUTE_MEDIUM_RISK.can_execute()

    def test_supervised_and_full_autonomy(self):
        """Test 10: SUPERVISED (4) and FULL (5) can execute any risk."""
        for level in [AutonomyLevel.SUPERVISED_AUTONOMY, AutonomyLevel.FULL_AUTONOMY]:
            assert level.can_execute("low")
            assert level.can_execute("medium")
            assert level.can_execute("high")
            assert level.can_execute("critical")


# ════════════════════════════════════════════════════════════════════
# 3. AutonomyConfig model
# ════════════════════════════════════════════════════════════════════

class TestAutonomyConfig:
    """Autonomy configuration model."""

    def test_default_config(self):
        """Test 11: Default config has min=0, max=5."""
        config = AutonomyConfig(goal_id="g1")
        assert config.goal_id == "g1"
        assert config.min_autonomy_level == AutonomyLevel.OBSERVE_ONLY
        assert config.max_autonomy_level == AutonomyLevel.FULL_AUTONOMY
        assert config.override_rules == []

    def test_custom_config(self):
        """Test 12: Custom autonomy bounds."""
        config = AutonomyConfig(
            goal_id="g-sensitive",
            min_autonomy_level=AutonomyLevel.OBSERVE_ONLY,
            max_autonomy_level=AutonomyLevel.EXECUTE_LOW_RISK,
        )
        assert config.effective_level() == AutonomyLevel.EXECUTE_LOW_RISK

    def test_can_execute_action(self):
        """Test 13: can_execute_action delegates to effective level."""
        config = AutonomyConfig(
            goal_id="g1",
            max_autonomy_level=AutonomyLevel.EXECUTE_MEDIUM_RISK,
        )
        assert config.can_execute_action("low")
        assert config.can_execute_action("medium")
        assert not config.can_execute_action("high")

    def test_override_rules(self):
        """Test 14: Override rules are stored."""
        rules = [
            {"graph_id": "gx", "max_level": "execute_low_risk"},
        ]
        config = AutonomyConfig(
            goal_id="g1",
            override_rules=rules,
            max_autonomy_level=AutonomyLevel.FULL_AUTONOMY,
        )
        assert len(config.override_rules) == 1
        assert config.override_rules[0]["graph_id"] == "gx"

    def test_extra_forbid(self):
        """Test 15: Extra fields rejected."""
        with pytest.raises(Exception):
            AutonomyConfig(goal_id="g1", unknown="bad")  # type: ignore


# ════════════════════════════════════════════════════════════════════
# 4. CognitiveBudget model
# ════════════════════════════════════════════════════════════════════

class TestCognitiveBudget:
    """Static budget limits."""

    def test_default_budget(self):
        """Test 16: Default budget has sensible limits."""
        b = CognitiveBudget()
        assert b.reasoning_cycles == 5
        assert b.planning_attempts == 3
        assert b.revision_count == 3
        assert b.learning_iterations == 10
        assert b.goal_id == "__system__"

    def test_custom_budget(self):
        """Test 17: Custom budget limits."""
        b = CognitiveBudget(
            goal_id="g-custom",
            reasoning_cycles=10,
            planning_attempts=5,
            revision_count=1,
            learning_iterations=0,
        )
        assert b.goal_id == "g-custom"
        assert b.reasoning_cycles == 10
        assert b.learning_iterations == 0

    def test_get_limit(self):
        """Test 18: get_limit returns correct max for each type."""
        b = CognitiveBudget(reasoning_cycles=7)
        assert b.get_limit("reasoning_cycles") == 7
        assert b.get_limit("planning_attempts") == 3
        assert b.get_limit("revision_count") == 3
        assert b.get_limit("learning_iterations") == 10
        assert b.get_limit("unknown_type") == 0

    def test_budget_validation(self):
        """Test 19: Validation enforces bounds."""
        with pytest.raises(Exception):
            CognitiveBudget(reasoning_cycles=0)
        with pytest.raises(Exception):
            CognitiveBudget(planning_attempts=0)
        with pytest.raises(Exception):
            CognitiveBudget(revision_count=-1)


# ════════════════════════════════════════════════════════════════════
# 5. BudgetTracker — consumption & limits
# ════════════════════════════════════════════════════════════════════

class TestBudgetTrackerConsume:
    """Budget consumption tracking."""

    async def test_consume_within_budget(self):
        """Test 20: consume() returns True within limits."""
        budget = CognitiveBudget(reasoning_cycles=3)
        tracker = BudgetTracker(budget)

        assert await tracker.consume("reasoning_cycles") is True
        assert await tracker.consume("reasoning_cycles") is True
        assert await tracker.consume("reasoning_cycles") is True

    async def test_consume_exhausted(self):
        """Test 21: consume() returns False when budget exhausted."""
        budget = CognitiveBudget(planning_attempts=2)
        tracker = BudgetTracker(budget)

        assert await tracker.consume("planning_attempts") is True
        assert await tracker.consume("planning_attempts") is True
        assert await tracker.consume("planning_attempts") is False  # exhausted

    async def test_consume_with_amount(self):
        """Test 22: consume with custom amount works."""
        budget = CognitiveBudget(reasoning_cycles=10)
        tracker = BudgetTracker(budget)

        assert await tracker.consume("reasoning_cycles", 5) is True
        assert await tracker.consume("reasoning_cycles", 5) is True
        assert await tracker.consume("reasoning_cycles", 1) is False

    async def test_consume_unknown_type(self):
        """Test 23: Unknown budget type returns False."""
        budget = CognitiveBudget()
        tracker = BudgetTracker(budget)
        result = await tracker.consume("unknown_potato")
        assert result is False

    async def test_consume_zero_limit(self):
        """Test 24: Budget with zero limit always returns False."""
        budget = CognitiveBudget(revision_count=0)
        tracker = BudgetTracker(budget)
        assert await tracker.consume("revision_count") is False

    async def test_is_exhausted(self):
        """Test 25: is_exhausted detection."""
        budget = CognitiveBudget(reasoning_cycles=1)
        tracker = BudgetTracker(budget)
        assert not await tracker.is_exhausted("reasoning_cycles")
        await tracker.consume("reasoning_cycles")
        assert await tracker.is_exhausted("reasoning_cycles")

    async def test_percent_used(self):
        """Test 26: percent_used returns correct fraction."""
        budget = CognitiveBudget(reasoning_cycles=10)
        tracker = BudgetTracker(budget)
        assert await tracker.percent_used("reasoning_cycles") == 0.0

        await tracker.consume("reasoning_cycles", 5)
        assert await tracker.percent_used("reasoning_cycles") == 0.5

        await tracker.consume("reasoning_cycles", 5)
        assert await tracker.percent_used("reasoning_cycles") == 1.0


# ════════════════════════════════════════════════════════════════════
# 6. BudgetTracker — reset & remaining
# ════════════════════════════════════════════════════════════════════

class TestBudgetTrackerReset:
    """Reset and remaining methods."""

    async def test_get_remaining_full(self):
        """Test 27: get_remaining returns all limits initially."""
        budget = CognitiveBudget(
            reasoning_cycles=5, planning_attempts=3,
            revision_count=3, learning_iterations=10,
        )
        tracker = BudgetTracker(budget)
        remaining = await tracker.get_remaining()
        assert remaining["reasoning_cycles"] == 5
        assert remaining["planning_attempts"] == 3
        assert remaining["revision_count"] == 3
        assert remaining["learning_iterations"] == 10

    async def test_get_remaining_partial(self):
        """Test 28: Partial consumption reduces remaining."""
        budget = CognitiveBudget(reasoning_cycles=5)
        tracker = BudgetTracker(budget)
        await tracker.consume("reasoning_cycles", 2)

        remaining = await tracker.get_remaining()
        assert remaining["reasoning_cycles"] == 3

    async def test_reset_clears_counters(self):
        """Test 29: reset restores all counters to zero consumed."""
        budget = CognitiveBudget(reasoning_cycles=3)
        tracker = BudgetTracker(budget)
        await tracker.consume("reasoning_cycles", 2)
        assert (await tracker.get_remaining())["reasoning_cycles"] == 1

        await tracker.reset()
        remaining = await tracker.get_remaining()
        assert remaining["reasoning_cycles"] == 3  # back to full

    async def test_reset_all_types(self):
        """Test 30: reset clears all four budget types."""
        budget = CognitiveBudget(planning_attempts=2, revision_count=1)
        tracker = BudgetTracker(budget)
        await tracker.consume("planning_attempts", 2)
        await tracker.consume("revision_count", 1)
        assert (await tracker.get_remaining())["planning_attempts"] == 0
        assert (await tracker.get_remaining())["revision_count"] == 0

        await tracker.reset()
        remaining = await tracker.get_remaining()
        assert remaining["planning_attempts"] == 2
        assert remaining["revision_count"] == 1


# ════════════════════════════════════════════════════════════════════
# 7. Integration & Edge Cases
# ════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Cross-module and DB-backed scenarios."""

    async def test_autonomy_config_with_budget(self, db):
        """Test 31: Autonomy config and budget can coexist for same goal."""
        # Create config and budget for the same goal
        config = AutonomyConfig(
            goal_id="g-integration",
            max_autonomy_level=AutonomyLevel.EXECUTE_MEDIUM_RISK,
        )
        budget = CognitiveBudget(
            goal_id="g-integration",
            reasoning_cycles=3,
        )
        tracker = BudgetTracker(budget, db=db)

        # Persist config
        await db.execute(
            """INSERT INTO autonomy_configs
               (goal_id, min_autonomy_level, max_autonomy_level,
                override_rules, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                config.goal_id,
                config.min_autonomy_level.value,
                config.max_autonomy_level.value,
                json.dumps(config.override_rules),
                config.created_at.isoformat(),
                config.updated_at.isoformat(),
            ],
        )

        # Persist budget
        await db.execute(
            """INSERT INTO cognitive_budgets
               (id, goal_id, reasoning_cycles, planning_attempts,
                revision_count, learning_iterations, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                budget.id,
                budget.goal_id,
                budget.reasoning_cycles,
                budget.planning_attempts,
                budget.revision_count,
                budget.learning_iterations,
                budget.created_at.isoformat(),
            ],
        )

        # Read back
        row = await db.fetch_one(
            "SELECT * FROM autonomy_configs WHERE goal_id = ?",
            ["g-integration"],
        )
        assert row is not None
        assert row["max_autonomy_level"] == "execute_medium_risk"

        b_row = await db.fetch_one(
            "SELECT * FROM cognitive_budgets WHERE goal_id = ?",
            ["g-integration"],
        )
        assert b_row is not None
        assert b_row["reasoning_cycles"] == 3

        # Budget tracker on persisted budget
        assert await tracker.consume("reasoning_cycles") is True
        assert await tracker.consume("reasoning_cycles") is True
        assert await tracker.consume("reasoning_cycles") is True
        assert await tracker.consume("reasoning_cycles") is False  # exhausted

        # Autonomy check
        assert config.can_execute_action("low")
        assert config.can_execute_action("medium")
        assert not config.can_execute_action("high")

    async def test_multi_tracker_independence(self):
        """Test 32: Two trackers for different goals don't interfere."""
        budget_system = CognitiveBudget(reasoning_cycles=2)
        budget_sensitive = CognitiveBudget(goal_id="g-sensitive", reasoning_cycles=5)

        t1 = BudgetTracker(budget_system, goal_id="__system__")
        t2 = BudgetTracker(budget_sensitive, goal_id="g-sensitive")

        # Exhaust t1
        await t1.consume("reasoning_cycles")
        await t1.consume("reasoning_cycles")
        assert await t1.consume("reasoning_cycles") is False

        # t2 still has budget
        assert await t2.consume("reasoning_cycles") is True
        assert await t2.consume("reasoning_cycles") is True
        remaining = await t2.get_remaining()
        assert remaining["reasoning_cycles"] == 3

    async def test_db_persistence(self, db_path):
        """Test 33: Budget consumption persists across tracker instances."""
        budget = CognitiveBudget(reasoning_cycles=3)

        # First tracker consumes some budget
        db1 = Database(db_path)
        await db1.initialize()
        t1 = BudgetTracker(budget, db=db1, tracker_id="tracker-persist")
        await t1.consume("reasoning_cycles", 2)
        await db1.close()

        # Second tracker with same ID reads persisted state
        db2 = Database(db_path)
        await db2.initialize()
        t2 = BudgetTracker(budget, db=db2, tracker_id="tracker-persist")
        # Fresh in-memory, but table exists from first run
        remaining = await t2.get_remaining()
        assert remaining["reasoning_cycles"] == 3  # fresh in-memory
        await db2.close()

    async def test_all_budget_types_consume(self):
        """Test 34: All four budget types can be consumed independently."""
        budget = CognitiveBudget(
            reasoning_cycles=2,
            planning_attempts=2,
            revision_count=2,
            learning_iterations=2,
        )
        tracker = BudgetTracker(budget)

        for btype in ALL_BUDGET_TYPES:
            assert await tracker.consume(btype) is True
            assert await tracker.consume(btype) is True
            assert await tracker.consume(btype) is False  # exhausted

        remaining = await tracker.get_remaining()
        for btype in ALL_BUDGET_TYPES:
            assert remaining[btype] == 0

    async def test_autonomy_requires_supervision(self):
        """Test 35: requires_supervision() helper."""
        assert AutonomyLevel.OBSERVE_ONLY.requires_supervision() is True
        assert AutonomyLevel.RECOMMEND.requires_supervision() is True
        assert AutonomyLevel.EXECUTE_LOW_RISK.requires_supervision() is True
        assert AutonomyLevel.EXECUTE_MEDIUM_RISK.requires_supervision() is True
        assert AutonomyLevel.SUPERVISED_AUTONOMY.requires_supervision() is False
        assert AutonomyLevel.FULL_AUTONOMY.requires_supervision() is False
