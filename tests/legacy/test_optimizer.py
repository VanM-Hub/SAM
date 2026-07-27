"""Tests for Self-Optimization Engine — Sprint 28 Fase 1.

ParamManager CRUD + SelfOptimizer analysis, apply, rollback,
history, and integration with InstitutionalMemory.
"""

import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import pytest_asyncio

from sam.persistence.database import Database
from sam.evolution.params import OptimizableParam, ParamManager, PARAM_CATEGORIES
from sam.evolution.optimizer import SelfOptimizer, OptimizationSuggestion, OptimizationGoal
from sam.institutional.memory import InstitutionalMemory, InstitutionalMemoryManager


# ═════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def db():
    """Create temporary database with all migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    database = Database(db_path)
    await database.initialize()
    from sam.persistence.migrations.manager import MigrationManager
    migrations_dir = Path(__file__).parent / "sam" / "persistence" / "migrations"
    manager = MigrationManager(database, str(migrations_dir))
    await manager.migrate()
    yield database
    await database.close()
    Path(db_path).unlink(missing_ok=True)


@pytest_asyncio.fixture
async def pm(db):
    return ParamManager(db)


@pytest_asyncio.fixture
async def imm(db):
    return InstitutionalMemoryManager(db)


@pytest_asyncio.fixture
async def optimizer(pm, imm):
    return SelfOptimizer(institutional_memory=imm, param_manager=pm)


@pytest_asyncio.fixture
async def seeded(db):
    """Seed some memory entries for analysis tests."""
    mgr = InstitutionalMemoryManager(db)
    entries = [
        InstitutionalMemory(
            id=f"test-mem-{i}",
            type="PATTERN",
            content={"cost": 500, "execution_cost": 500},
            source="optimizer-test",
            confidence=0.8,
            success_count=10 - i,
            failure_count=i,
        )
        for i in range(5)
    ]
    for e in entries:
        await mgr.store(e)
    return mgr


# ═══════════════════════════════════════════════
# OptimizableParam model tests
# ═══════════════════════════════════════════════

class TestOptimizableParamModel:
    def test_create_minimal(self):
        p = OptimizableParam(id="p1", name="test.param", current_value=0.5)
        assert p.category == "RANKING"
        assert p.description == ""

    def test_create_all_fields(self):
        p = OptimizableParam(
            id="p2", name="scheduler.interval", current_value=60,
            min_value=5, max_value=3600, step=5,
            category="SCHEDULER", description="Poll interval",
        )
        assert p.category == "SCHEDULER"
        assert p.min_value == 5

    def test_invalid_category_raises(self):
        with pytest.raises(ValueError, match="Invalid category"):
            OptimizableParam(id="p3", name="bad", current_value=0, category="BOGUS")

    def test_param_categories_enum(self):
        assert sorted(PARAM_CATEGORIES) == sorted(["RANKING", "SCHEDULER", "RETRY", "BUDGET", "TEMPLATE"])

    def test_to_dict_and_from_dict_roundtrip(self):
        p = OptimizableParam(
            id="p-rt", name="ranking.weights.risk", current_value=0.3,
            min_value=0.0, max_value=1.0, step=0.05,
            category="RANKING", description="Risk weight",
        )
        d = p.to_dict()
        p2 = OptimizableParam.from_dict(d)
        assert p2.id == p.id
        assert p2.name == p.name
        assert p2.current_value == pytest.approx(0.3)
        assert p2.min_value == pytest.approx(0.0)
        assert p2.category == "RANKING"

    def test_to_dict_with_none_bounds(self):
        p = OptimizableParam(id="p-nb", name="unbounded", current_value=42)
        d = p.to_dict()
        assert d["min_value"] is None
        assert d["max_value"] is None

    def test_repr(self):
        p = OptimizableParam(id="p-rp", name="test.repr", current_value=1.0)
        r = repr(p)
        assert "test.repr" in r
        assert "RANKING" in r

    def test_json_value_parsing(self):
        """Ensure current_value roundtrips through JSON for complex types."""
        p = OptimizableParam(id="p-jp", name="complex", current_value=[1, 2, 3])
        d = p.to_dict()
        p2 = OptimizableParam.from_dict(d)
        assert p2.current_value == [1, 2, 3]

    def test_json_value_string(self):
        """String values should survive JSON roundtrip."""
        p = OptimizableParam(id="p-str", name="str.val", current_value="hello")
        d = p.to_dict()
        p2 = OptimizableParam.from_dict(d)
        assert p2.current_value == "hello"

    def test_from_dict_with_raw_values(self):
        """from_dict handles non-JSON-serialized values gracefully."""
        p = OptimizableParam.from_dict({
            "id": "p-raw",
            "name": "raw",
            "current_value": "42",
            "category": "RANKING",
            "description": "",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        })
        # current_value "42" as string: _parse_json tries json.loads("42") which returns int 42
        assert p.current_value == 42


# ═══════════════════════════════════════════════
# ParamManager tests
# ═══════════════════════════════════════════════

class TestParamManagerDefaults:
    @pytest.mark.asyncio
    async def test_register_defaults_creates_all(self, pm):
        await pm.register_defaults()
        params = await pm.list()
        assert len(params) == 9  # 9 defaults defined

    @pytest.mark.asyncio
    async def test_register_defaults_idempotent(self, pm):
        await pm.register_defaults()
        await pm.register_defaults()  # second call should not error
        params = await pm.list()
        assert len(params) == 9

    @pytest.mark.asyncio
    async def test_defaults_have_correct_categories(self, pm):
        await pm.register_defaults()
        for cat in PARAM_CATEGORIES:
            params = await pm.list(category=cat)
            assert len(params) >= 1, f"No defaults for {cat}"


class TestParamManagerGet:
    @pytest.mark.asyncio
    async def test_get_existing(self, pm):
        await pm.register_defaults()
        p = await pm.get("ranking.weights.risk")
        assert p is not None
        assert p.current_value == pytest.approx(0.3)

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, pm):
        p = await pm.get("nonexistent.param")
        assert p is None

    @pytest.mark.asyncio
    async def test_get_returns_correct_category(self, pm):
        await pm.register_defaults()
        p = await pm.get("retry.max_attempts")
        assert p.category == "RETRY"
        assert p.current_value == 3


class TestParamManagerSet:
    @pytest.mark.asyncio
    async def test_set_value(self, pm):
        await pm.register_defaults()
        await pm.set("ranking.weights.risk", 0.5)
        p = await pm.get("ranking.weights.risk")
        assert p.current_value == pytest.approx(0.5)

    @pytest.mark.asyncio
    async def test_set_updates_timestamp(self, pm):
        await pm.register_defaults()
        before = datetime.now(timezone.utc)
        await pm.set("ranking.weights.risk", 0.5)
        p = await pm.get("ranking.weights.risk")
        assert p.last_updated is not None

    @pytest.mark.asyncio
    async def test_set_nonexistent_raises(self, pm):
        with pytest.raises(ValueError, match="not found"):
            await pm.set("ghost.param", 42)


class TestParamManagerList:
    @pytest.mark.asyncio
    async def test_list_empty(self, pm):
        params = await pm.list()
        assert params == []

    @pytest.mark.asyncio
    async def test_list_by_category(self, pm):
        await pm.register_defaults()
        ranking = await pm.list(category="RANKING")
        assert len(ranking) >= 3
        for p in ranking:
            assert p.category == "RANKING"

    @pytest.mark.asyncio
    async def test_list_invalid_category_raises(self, pm):
        with pytest.raises(ValueError, match="Invalid category"):
            await pm.list(category="BOGUS")


# ═══════════════════════════════════════════════
# SelfOptimizer analysis tests
# ═══════════════════════════════════════════════

class TestSelfOptimizerAnalyze:
    @pytest.mark.asyncio
    async def test_analyze_success_rate_no_memory(self, optimizer, pm):
        await pm.register_defaults()
        suggestions = await optimizer.analyze(OptimizationGoal.MAXIMIZE_SUCCESS_RATE)
        # Without memory entries, should still produce some suggestions
        assert len(suggestions) >= 1

    @pytest.mark.asyncio
    async def test_analyze_with_seeded_memory(self, optimizer, pm, seeded):
        await pm.register_defaults()
        suggestions = await optimizer.analyze(OptimizationGoal.MAXIMIZE_SUCCESS_RATE)
        assert len(suggestions) >= 1
        # Suggestions should have confidence > 0
        for s in suggestions:
            assert 0.0 <= s.confidence <= 1.0
            assert s.expected_improvement >= 0.0

    @pytest.mark.asyncio
    async def test_analyze_duration(self, optimizer, pm, seeded):
        await pm.register_defaults()
        suggestions = await optimizer.analyze(OptimizationGoal.MINIMIZE_DURATION)
        assert len(suggestions) >= 1
        for s in suggestions:
            assert s.param_name is not None

    @pytest.mark.asyncio
    async def test_analyze_cost(self, optimizer, pm, seeded):
        await pm.register_defaults()
        suggestions = await optimizer.analyze(OptimizationGoal.MINIMIZE_COST)
        assert len(suggestions) >= 1

    @pytest.mark.asyncio
    async def test_analyze_balanced(self, optimizer, pm, seeded):
        await pm.register_defaults()
        suggestions = await optimizer.analyze(OptimizationGoal.BALANCED)
        assert len(suggestions) >= 1
        # Balanced should merge suggestions, possibly fewer dups
        assert len(suggestions) <= 6  # max distinct params we could suggest

    @pytest.mark.asyncio
    async def test_suggestions_sorted_by_improvement(self, optimizer, pm, seeded):
        await pm.register_defaults()
        suggestions = await optimizer.analyze(OptimizationGoal.MAXIMIZE_SUCCESS_RATE)
        for i in range(len(suggestions) - 1):
            assert suggestions[i].expected_improvement >= suggestions[i + 1].expected_improvement

    @pytest.mark.asyncio
    async def test_suggestion_has_evidence(self, optimizer, pm, seeded):
        await pm.register_defaults()
        suggestions = await optimizer.analyze(OptimizationGoal.MAXIMIZE_SUCCESS_RATE)
        if suggestions:
            s = suggestions[0]
            assert isinstance(s.evidence, list)


class TestSelfOptimizerSuggestionModel:
    def test_suggestion_creation(self):
        s = OptimizationSuggestion(
            param_name="test.param",
            current_value=0.3,
            suggested_value=0.5,
            expected_improvement=10.0,
            confidence=0.8,
            evidence=["ev-1", "ev-2"],
        )
        assert s.expected_improvement == 10.0

    def test_suggestion_to_dict(self):
        s = OptimizationSuggestion(
            param_name="test.param",
            current_value=0.3,
            suggested_value=0.5,
            expected_improvement=10.0,
            confidence=0.8,
            evidence=["ev-1"],
        )
        d = s.to_dict()
        assert d["param_name"] == "test.param"
        assert d["expected_improvement"] == 10.0

    def test_suggestion_default_evidence(self):
        s = OptimizationSuggestion(
            param_name="test.param",
            current_value=0.3,
            suggested_value=0.5,
            expected_improvement=5.0,
            confidence=0.5,
        )
        assert s.evidence == []


# ═══════════════════════════════════════════════
# SelfOptimizer apply tests
# ═══════════════════════════════════════════════

class TestSelfOptimizerApply:
    @pytest.mark.asyncio
    async def test_apply_suggestion(self, optimizer, pm):
        await pm.register_defaults()
        s = OptimizationSuggestion(
            param_name="retry.max_attempts",
            current_value=3,
            suggested_value=5,
            expected_improvement=15.0,
            confidence=0.7,
            evidence=["ev-1"],
        )
        history_id = await optimizer.apply_suggestion(s)
        assert history_id is not None
        # Verify parameter was updated
        p = await pm.get("retry.max_attempts")
        assert p.current_value == 5

    @pytest.mark.asyncio
    async def test_apply_suggestion_creates_history(self, optimizer, pm):
        await pm.register_defaults()
        s = OptimizationSuggestion(
            param_name="ranking.weights.risk",
            current_value=0.3,
            suggested_value=0.4,
            expected_improvement=5.0,
            confidence=0.6,
        )
        await optimizer.apply_suggestion(s)
        history = await optimizer.get_optimization_history()
        assert len(history) == 1
        assert history[0]["param_name"] == "ranking.weights.risk"
        assert history[0]["new_value"] == pytest.approx(0.4)

    @pytest.mark.asyncio
    async def test_apply_nonexistent_param_raises(self, optimizer):
        s = OptimizationSuggestion(
            param_name="ghost.param",
            current_value=0,
            suggested_value=1,
            expected_improvement=10.0,
            confidence=0.5,
        )
        with pytest.raises(ValueError, match="not found"):
            await optimizer.apply_suggestion(s)

    @pytest.mark.asyncio
    async def test_apply_history_stores_evidence(self, optimizer, pm):
        await pm.register_defaults()
        s = OptimizationSuggestion(
            param_name="retry.max_attempts",
            current_value=3,
            suggested_value=4,
            expected_improvement=8.0,
            confidence=0.6,
            evidence=["mem-1", "mem-2"],
        )
        await optimizer.apply_suggestion(s)
        history = await optimizer.get_optimization_history()
        # evidence is already parsed by get_optimization_history
        assert history[0]["evidence"] == ["mem-1", "mem-2"]


class TestSelfOptimizerHistory:
    @pytest.mark.asyncio
    async def test_empty_history(self, optimizer):
        history = await optimizer.get_optimization_history()
        assert history == []

    @pytest.mark.asyncio
    async def test_history_limit(self, optimizer, pm):
        await pm.register_defaults()
        for i in range(10):
            s = OptimizationSuggestion(
                param_name="retry.max_attempts",
                current_value=3,
                suggested_value=3 + i,
                expected_improvement=float(i),
                confidence=0.5,
            )
            await optimizer.apply_suggestion(s)
        history = await optimizer.get_optimization_history(limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_history_ordered_by_date(self, optimizer, pm):
        await pm.register_defaults()
        for i in range(3):
            s = OptimizationSuggestion(
                param_name="retry.max_attempts",
                current_value=3,
                suggested_value=3 + i,
                expected_improvement=float(i * 5),
                confidence=0.5,
            )
            await optimizer.apply_suggestion(s)
        history = await optimizer.get_optimization_history()
        assert len(history) == 3
        # Most recent first
        assert history[0]["new_value"] == 5  # last applied


class TestSelfOptimizerRollback:
    @pytest.mark.asyncio
    async def test_rollback_most_recent(self, optimizer, pm):
        await pm.register_defaults()
        # Apply two changes
        s1 = OptimizationSuggestion("retry.max_attempts", 3, 5, 10.0, 0.7)
        await optimizer.apply_suggestion(s1)
        s2 = OptimizationSuggestion("retry.max_attempts", 5, 7, 10.0, 0.7)
        await optimizer.apply_suggestion(s2)

        assert (await pm.get("retry.max_attempts")).current_value == 7
        await optimizer.rollback("retry.max_attempts", version=0)
        assert (await pm.get("retry.max_attempts")).current_value == 5

    @pytest.mark.asyncio
    async def test_rollback_older_version(self, optimizer, pm):
        await pm.register_defaults()
        await optimizer.apply_suggestion(
            OptimizationSuggestion("retry.max_attempts", 3, 5, 10.0, 0.7)
        )
        await optimizer.apply_suggestion(
            OptimizationSuggestion("retry.max_attempts", 5, 7, 10.0, 0.7)
        )
        await optimizer.rollback("retry.max_attempts", version=1)
        assert (await pm.get("retry.max_attempts")).current_value == 3

    @pytest.mark.asyncio
    async def test_rollback_no_history_raises(self, optimizer, pm):
        await pm.register_defaults()
        with pytest.raises(ValueError, match="No optimization history"):
            await optimizer.rollback("retry.max_attempts")

    @pytest.mark.asyncio
    async def test_rollback_version_out_of_range_raises(self, optimizer, pm):
        await pm.register_defaults()
        await optimizer.apply_suggestion(
            OptimizationSuggestion("retry.max_attempts", 3, 5, 10.0, 0.7)
        )
        with pytest.raises(ValueError, match="out of range"):
            await optimizer.rollback("retry.max_attempts", version=5)

    @pytest.mark.asyncio
    async def test_rollback_creates_new_history_entry(self, optimizer, pm):
        await pm.register_defaults()
        await optimizer.apply_suggestion(
            OptimizationSuggestion("retry.max_attempts", 3, 5, 10.0, 0.7)
        )
        before = await optimizer.get_optimization_history()
        assert len(before) == 1
        await optimizer.rollback("retry.max_attempts")
        after = await optimizer.get_optimization_history()
        assert len(after) == 2
        # Most recent should be the rollback (restoring to 3)
        assert after[0]["new_value"] == 3
