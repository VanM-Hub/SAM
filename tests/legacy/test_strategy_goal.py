"""Tests for Strategic Goal & Long-Term Objective — Sprint 27 Fase 1.

Strategic goal CRUD, hierarchy tree, progress evaluation, metrics update;
Long-term objective management and aggregate progress.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pytest
import pytest_asyncio

from sam.persistence.database import Database
from sam.strategy.goal import (
    GOAL_HORIZONS,
    GOAL_STATUSES,
    StrategicGoal,
    StrategicGoalManager,
)
from sam.strategy.objective import (
    OBJECTIVE_STATUSES,
    LongTermObjective,
    ObjectiveManager,
)


@pytest_asyncio.fixture
async def db():
    """Create temporary database with all migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    database = Database(db_path)
    await database.initialize()
    from sam.persistence.migrations.manager import MigrationManager
    migrations_dir = Path(__file__).parent.parent / "sam" / "persistence" / "migrations"
    manager = MigrationManager(database, str(migrations_dir))
    await manager.migrate()
    yield database
    await database.close()
    Path(db_path).unlink(missing_ok=True)


@pytest_asyncio.fixture
async def sgm(db):
    return StrategicGoalManager(db)


@pytest_asyncio.fixture
async def om(db):
    return ObjectiveManager(db)


def make_goal(
    id: str = "sg-1",
    name: str = "Achieve 99.9% Reliability",
    horizon: str = "LONG_TERM",
    target: Optional[Dict[str, float]] = None,
    current: Optional[Dict[str, float]] = None,
    status: str = "ACTIVE",
    priority: int = 8,
    parent: Optional[str] = None,
) -> StrategicGoal:
    return StrategicGoal(
        id=id,
        name=name,
        description="Strategic goal for testing",
        horizon=horizon,
        target_metrics=target or {"reliability": 0.999},
        current_metrics=current or {"reliability": 0.85},
        status=status,
        priority=priority,
        parent_goal_id=parent,
    )


def make_objective(
    id: str = "obj-1",
    description: str = "Achieve platform excellence",
    goal_ids: Optional[List[str]] = None,
    status: str = "ACTIVE",
) -> LongTermObjective:
    return LongTermObjective(
        id=id,
        description=description,
        strategic_goal_ids=goal_ids or [],
        timeline={"milestones": ["Q1 target", "Q2 release"], "deadline": "2026-12-31"},
        status=status,
    )


# ═══════════════════════════════════════════════
# StrategicGoal model tests
# ═══════════════════════════════════════════════

class TestStrategicGoalModel:
    def test_create_minimal(self):
        g = StrategicGoal(id="sg-m", name="Min Goal")
        assert g.status == "ACTIVE"
        assert g.horizon == "LONG_TERM"
        assert g.priority == 5
        assert g.target_metrics == {}
        assert g.current_metrics == {}

    def test_create_with_all_fields(self):
        g = StrategicGoal(
            id="sg-full",
            name="Full Goal",
            description="A complete goal",
            horizon="SHORT_TERM",
            target_metrics={"uptime": 99.5},
            current_metrics={"uptime": 97.0},
            status="PAUSED",
            priority=10,
            parent_goal_id="sg-parent",
        )
        assert g.horizon == "SHORT_TERM"
        assert g.status == "PAUSED"
        assert g.priority == 10
        assert g.parent_goal_id == "sg-parent"

    def test_invalid_horizon_raises(self):
        with pytest.raises(ValueError, match="Invalid horizon"):
            StrategicGoal(id="sg-bh", name="Bad", horizon="YESTERDAY")

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            StrategicGoal(id="sg-bs", name="Bad", status="UNKNOWN")

    def test_invalid_priority_low_raises(self):
        with pytest.raises(ValueError, match="Priority must be between 1 and 10"):
            StrategicGoal(id="sg-pl", name="Bad", priority=0)

    def test_invalid_priority_high_raises(self):
        with pytest.raises(ValueError, match="Priority must be between 1 and 10"):
            StrategicGoal(id="sg-ph", name="Bad", priority=11)

    def test_goal_horizons_enum(self):
        assert sorted(GOAL_HORIZONS) == sorted(["SHORT_TERM", "MEDIUM_TERM", "LONG_TERM"])

    def test_goal_statuses_enum(self):
        assert sorted(GOAL_STATUSES) == sorted(["ACTIVE", "PAUSED", "COMPLETED", "FAILED", "ARCHIVED"])

    def test_to_dict_and_from_dict_roundtrip(self):
        g = make_goal(
            id="sg-rt",
            name="Roundtrip Goal",
            target={"reliability": 0.999, "latency_ms": 100},
            current={"reliability": 0.92, "latency_ms": 120},
        )
        d = g.to_dict()
        g2 = StrategicGoal.from_dict(d)
        assert g2.id == g.id
        assert g2.name == g.name
        assert g2.target_metrics == g.target_metrics
        assert g2.current_metrics == g.current_metrics
        assert g2.priority == g.priority

    def test_from_dict_with_json_strings(self):
        d = {
            "id": "sg-js",
            "name": "JSON Goal",
            "description": "",
            "horizon": "MEDIUM_TERM",
            "target_metrics": '{"accuracy": 0.95}',
            "current_metrics": '{"accuracy": 0.88}',
            "status": "ACTIVE",
            "priority": 6,
            "parent_goal_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        g = StrategicGoal.from_dict(d)
        assert g.horizon == "MEDIUM_TERM"
        assert g.target_metrics == {"accuracy": 0.95}
        assert g.current_metrics == {"accuracy": 0.88}

    def test_evaluate_progress_full(self):
        g = make_goal(
            target={"reliability": 0.999, "latency_ms": 100},
            current={"reliability": 0.85, "latency_ms": 120},
        )
        # reliability: 0.85/0.999 = 0.85085, latency: 120/100 clamped = 1.0
        # avg = (0.85085 + 1.0) / 2 = 0.9254
        p = g.evaluate_progress()
        assert p > 0.9 and p < 0.95

    def test_evaluate_progress_empty_target(self):
        g = StrategicGoal(id="sg-ep", name="No target")
        assert g.evaluate_progress() == 0.0

    def test_evaluate_progress_all_vs_none(self):
        g = StrategicGoal(
            id="sg-an",
            name="All vs None",
            target_metrics={"reliability": 0.0},
        )
        assert g.evaluate_progress() == 0.0  # skip zero-targets

    def test_evaluate_progress_overshoot_clamped(self):
        g = make_goal(
            target={"x": 10.0},
            current={"x": 50.0},
        )
        assert g.evaluate_progress() == 1.0


# ═══════════════════════════════════════════════
# StrategicGoalManager CRUD tests
# ═══════════════════════════════════════════════

class TestStrategicGoalManagerCreate:
    @pytest.mark.asyncio
    async def test_create_goal(self, sgm, db):
        g = make_goal()
        goal_id = await sgm.create_goal(g)
        assert goal_id == "sg-1"
        row = await db.fetch_one(
            "SELECT * FROM strategic_goals WHERE id = ?", (goal_id,)
        )
        assert row is not None
        assert row["name"] == "Achieve 99.9% Reliability"

    @pytest.mark.asyncio
    async def test_get_goal(self, sgm):
        g = make_goal(id="sg-get")
        await sgm.create_goal(g)
        found = await sgm.get_goal("sg-get")
        assert found is not None
        assert found.name == "Achieve 99.9% Reliability"

    @pytest.mark.asyncio
    async def test_get_goal_nonexistent(self, sgm):
        found = await sgm.get_goal("ghost-sg")
        assert found is None


class TestStrategicGoalManagerUpdateMetrics:
    @pytest.mark.asyncio
    async def test_update_metrics(self, sgm):
        g = make_goal(
            id="sg-um",
            target={"reliability": 0.999},
            current={"reliability": 0.8},
        )
        await sgm.create_goal(g)
        await sgm.update_metrics("sg-um", {"reliability": 0.95, "latency_ms": 50})

        updated = await sgm.get_goal("sg-um")
        assert updated.current_metrics["reliability"] == 0.95
        assert updated.current_metrics["latency_ms"] == 50

    @pytest.mark.asyncio
    async def test_update_metrics_merge(self, sgm):
        g = make_goal(
            id="sg-merge",
            target={"a": 1.0, "b": 1.0},
            current={"a": 0.5},
        )
        await sgm.create_goal(g)
        await sgm.update_metrics("sg-merge", {"b": 0.7})
        updated = await sgm.get_goal("sg-merge")
        assert updated.current_metrics["a"] == 0.5
        assert updated.current_metrics["b"] == 0.7

    @pytest.mark.asyncio
    async def test_update_metrics_nonexistent(self, sgm):
        with pytest.raises(ValueError, match="Strategic goal not found"):
            await sgm.update_metrics("ghost-sg", {"x": 1.0})


class TestStrategicGoalManagerUpdateStatus:
    @pytest.mark.asyncio
    async def test_update_status(self, sgm):
        g = make_goal(id="sg-us")
        await sgm.create_goal(g)
        await sgm.update_status("sg-us", "COMPLETED")
        updated = await sgm.get_goal("sg-us")
        assert updated.status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_update_status_invalid(self, sgm):
        with pytest.raises(ValueError, match="Invalid status"):
            await sgm.update_status("sg-us-bad", "BOGUS")

    @pytest.mark.asyncio
    async def test_update_status_nonexistent(self, sgm):
        with pytest.raises(ValueError, match="Strategic goal not found"):
            await sgm.update_status("ghost-sg", "PAUSED")


class TestStrategicGoalManagerList:
    @pytest.mark.asyncio
    async def test_list_goals(self, sgm):
        for i in range(3):
            await sgm.create_goal(make_goal(id=f"sg-lst-{i}", name=f"Goal {i}"))
        goals = await sgm.list_goals()
        assert len(goals) >= 3

    @pytest.mark.asyncio
    async def test_list_goals_by_status(self, sgm):
        await sgm.create_goal(make_goal(id="sg-ls1", status="ACTIVE"))
        await sgm.create_goal(make_goal(id="sg-ls2", status="PAUSED"))
        active = await sgm.list_goals(status="ACTIVE")
        assert len(active) == 1
        assert active[0].id == "sg-ls1"

    @pytest.mark.asyncio
    async def test_list_goals_by_horizon(self, sgm):
        await sgm.create_goal(make_goal(id="sg-lh1", horizon="SHORT_TERM"))
        await sgm.create_goal(make_goal(id="sg-lh2", horizon="LONG_TERM"))
        short = await sgm.list_goals(horizon="SHORT_TERM")
        assert len(short) == 1

    @pytest.mark.asyncio
    async def test_list_goals_invalid_status(self, sgm):
        with pytest.raises(ValueError, match="Invalid status"):
            await sgm.list_goals(status="BOGUS")


# ═══════════════════════════════════════════════
# StrategicGoalManager hierarchy tests
# ═══════════════════════════════════════════════

class TestStrategicGoalManagerHierarchy:
    @pytest.mark.asyncio
    async def test_get_goal_tree(self, sgm):
        parent = make_goal(id="sg-parent", name="Parent")
        child = make_goal(id="sg-child", name="Child", parent="sg-parent")
        await sgm.create_goal(parent)
        await sgm.create_goal(child)
        tree = await sgm.get_goal_tree("sg-parent")
        assert tree["id"] == "sg-parent"
        assert len(tree["children"]) == 1
        assert tree["children"][0]["id"] == "sg-child"

    @pytest.mark.asyncio
    async def test_get_goal_tree_leaf(self, sgm):
        g = make_goal(id="sg-leaf")
        await sgm.create_goal(g)
        tree = await sgm.get_goal_tree("sg-leaf")
        assert tree["children"] == []

    @pytest.mark.asyncio
    async def test_get_goal_tree_nonexistent(self, sgm):
        with pytest.raises(ValueError, match="Strategic goal not found"):
            await sgm.get_goal_tree("ghost-sg")


# ═══════════════════════════════════════════════
# StrategicGoalManager progress evaluation tests
# ═══════════════════════════════════════════════

class TestStrategicGoalManagerEvaluate:
    @pytest.mark.asyncio
    async def test_evaluate_progress_own_only(self, sgm):
        g = make_goal(
            id="sg-epo",
            target={"reliability": 1.0},
            current={"reliability": 0.5},
        )
        await sgm.create_goal(g)
        p = await sgm.evaluate_progress("sg-epo")
        assert p == 0.5

    @pytest.mark.asyncio
    async def test_evaluate_progress_with_children(self, sgm):
        parent = make_goal(
            id="sg-epc",
            name="Parent",
            target={"x": 1.0},
            current={"x": 1.0},
        )
        child = make_goal(
            id="sg-epc-child",
            name="Child",
            target={"x": 1.0},
            current={"x": 0.0},
            parent="sg-epc",
        )
        await sgm.create_goal(parent)
        await sgm.create_goal(child)
        p = await sgm.evaluate_progress("sg-epc")
        # own=1.0, child=0.0 → 0.5 * 1.0 + 0.5 * 0.0 = 0.5
        assert p == 0.5

    @pytest.mark.asyncio
    async def test_evaluate_progress_nonexistent(self, sgm):
        with pytest.raises(ValueError, match="Strategic goal not found"):
            await sgm.evaluate_progress("ghost-sg")


# ═══════════════════════════════════════════════
# LongTermObjective model tests
# ═══════════════════════════════════════════════

class TestLongTermObjectiveModel:
    def test_create_minimal(self):
        o = LongTermObjective(id="obj-m", description="Min objective")
        assert o.status == "ACTIVE"
        assert o.strategic_goal_ids == []

    def test_create_with_all_fields(self):
        o = LongTermObjective(
            id="obj-full",
            description="Full objective",
            strategic_goal_ids=["sg-1", "sg-2"],
            timeline={"milestone": "Q1", "deadline": "2026-12-31"},
            status="ACHIEVED",
        )
        assert o.status == "ACHIEVED"
        assert len(o.strategic_goal_ids) == 2
        assert o.timeline["milestone"] == "Q1"

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            LongTermObjective(id="obj-bs", description="Bad", status="UNKNOWN")

    def test_objective_statuses_enum(self):
        assert sorted(OBJECTIVE_STATUSES) == sorted(["ACTIVE", "ACHIEVED", "ABANDONED"])

    def test_to_dict_and_from_dict_roundtrip(self):
        o = make_objective(
            id="obj-rt",
            goal_ids=["sg-a", "sg-b"],
        )
        d = o.to_dict()
        o2 = LongTermObjective.from_dict(d)
        assert o2.id == o.id
        assert o2.description == o.description
        assert o2.strategic_goal_ids == ["sg-a", "sg-b"]

    def test_from_dict_with_json_strings(self):
        d = {
            "id": "obj-js",
            "description": "JSON obj",
            "strategic_goal_ids": '["sg-x", "sg-y"]',
            "timeline": '{"deadline": "2026-12-31"}',
            "status": "ACTIVE",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        o = LongTermObjective.from_dict(d)
        assert o.strategic_goal_ids == ["sg-x", "sg-y"]
        assert o.timeline["deadline"] == "2026-12-31"


# ═══════════════════════════════════════════════
# ObjectiveManager tests
# ═══════════════════════════════════════════════

class TestObjectiveManagerCreate:
    @pytest.mark.asyncio
    async def test_create_objective(self, om, db):
        o = make_objective()
        obj_id = await om.create_objective(o)
        assert obj_id == "obj-1"
        row = await db.fetch_one(
            "SELECT * FROM long_term_objectives WHERE id = ?", (obj_id,)
        )
        assert row is not None
        assert row["description"] == "Achieve platform excellence"

    @pytest.mark.asyncio
    async def test_get_objective(self, om):
        o = make_objective(id="obj-get")
        await om.create_objective(o)
        found = await om.get_objective("obj-get")
        assert found is not None
        assert found.description == "Achieve platform excellence"

    @pytest.mark.asyncio
    async def test_get_objective_nonexistent(self, om):
        found = await om.get_objective("ghost-obj")
        assert found is None


class TestObjectiveManagerUpdate:
    @pytest.mark.asyncio
    async def test_update_status(self, om):
        o = make_objective(id="obj-upd")
        await om.create_objective(o)
        await om.update_status("obj-upd", "ACHIEVED")
        updated = await om.get_objective("obj-upd")
        assert updated.status == "ACHIEVED"

    @pytest.mark.asyncio
    async def test_update_status_invalid(self, om):
        with pytest.raises(ValueError, match="Invalid status"):
            await om.update_status("obj-none", "BOGUS")

    @pytest.mark.asyncio
    async def test_update_status_nonexistent(self, om):
        with pytest.raises(ValueError, match="Long-term objective not found"):
            await om.update_status("ghost-obj", "ABANDONED")


class TestObjectiveManagerGoalLinks:
    @pytest.mark.asyncio
    async def test_add_strategic_goal(self, om):
        o = make_objective(id="obj-add")
        await om.create_objective(o)
        await om.add_strategic_goal("obj-add", "sg-1")
        updated = await om.get_objective("obj-add")
        assert "sg-1" in updated.strategic_goal_ids

    @pytest.mark.asyncio
    async def test_add_duplicate_strategic_goal(self, om):
        o = make_objective(id="obj-dup", goal_ids=["sg-1"])
        await om.create_objective(o)
        await om.add_strategic_goal("obj-dup", "sg-1")
        updated = await om.get_objective("obj-dup")
        assert updated.strategic_goal_ids == ["sg-1"]  # no dupes

    @pytest.mark.asyncio
    async def test_remove_strategic_goal(self, om):
        o = make_objective(id="obj-rm", goal_ids=["sg-1", "sg-2"])
        await om.create_objective(o)
        await om.remove_strategic_goal("obj-rm", "sg-1")
        updated = await om.get_objective("obj-rm")
        assert updated.strategic_goal_ids == ["sg-2"]


class TestObjectiveManagerProgress:
    @pytest.mark.asyncio
    async def test_get_progress_no_goals(self, om):
        o = make_objective(id="obj-pr0")
        await om.create_objective(o)
        p = await om.get_objective_progress("obj-pr0")
        assert p == 0.0

    @pytest.mark.asyncio
    async def test_get_progress_with_goals(self, om, sgm, db):
        # Create strategic goals for the objective to reference
        g1 = make_goal(
            id="sg-pr1",
            target={"reliability": 1.0},
            current={"reliability": 1.0},
        )
        g2 = make_goal(
            id="sg-pr2",
            target={"reliability": 1.0},
            current={"reliability": 0.0},
        )
        await sgm.create_goal(g1)
        await sgm.create_goal(g2)

        o = make_objective(id="obj-pr1", goal_ids=["sg-pr1", "sg-pr2"])
        await om.create_objective(o)

        p = await om.get_objective_progress("obj-pr1", goal_manager=sgm)
        # (1.0 + 0.0) / 2 = 0.5
        assert p == 0.5


class TestObjectiveManagerList:
    @pytest.mark.asyncio
    async def test_list_objectives(self, om):
        for i in range(3):
            await om.create_objective(make_objective(id=f"obj-lst-{i}"))
        objs = await om.list_objectives()
        assert len(objs) >= 3

    @pytest.mark.asyncio
    async def test_list_objectives_by_status(self, om):
        await om.create_objective(make_objective(id="obj-la1", status="ACTIVE"))
        await om.create_objective(make_objective(id="obj-la2", status="ACHIEVED"))
        active = await om.list_objectives(status="ACTIVE")
        assert len(active) == 1

    @pytest.mark.asyncio
    async def test_list_objectives_invalid_status(self, om):
        with pytest.raises(ValueError, match="Invalid status"):
            await om.list_objectives(status="BOGUS")
