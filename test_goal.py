"""
Sprint 24 – Fase 1 Tests: Goal Model, Goal Tree, Progress Evaluation

Covers:
  1. Goal model construction and validation       (tests 1-4)
  2. GoalStatus transitions                       (tests 5-7)
  3. GoalTreeManager add/get goals                (tests 8-10)
  4. Goal Tree hierarchy                          (tests 11-14)
  5. Goal progress evaluation                     (tests 15-19)
  6. Edge cases and error handling                (tests 20-22)
"""

import json
import os
import tempfile
import pytest
from datetime import datetime

from sam.cognitive.goal import Goal, GoalStatus
from sam.cognitive.goal_tree import GoalTree, GoalTreeManager
from sam.persistence.database import Database


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def db_path():
    """Provide a temporary database path."""
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
    """Provide an initialized Database."""
    database = Database(db_path)
    await database.initialize()
    yield database
    # DB cleanup handled by db_path fixture


@pytest.fixture
async def manager(db):
    """Provide a GoalTreeManager connected to the test DB."""
    mgr = GoalTreeManager(db)
    await mgr._ensure_loaded()
    return mgr


# ════════════════════════════════════════════════════════════════════
# 1. Goal Model
# ════════════════════════════════════════════════════════════════════


class TestGoalModel:
    """Tests for the Goal Pydantic model."""

    def test_goal_defaults(self):
        """Test 1: Goal created with minimal fields gets sensible defaults."""
        goal = Goal(name="Test Goal")
        assert goal.id is not None
        assert len(goal.id) == 12
        assert goal.name == "Test Goal"
        assert goal.description == ""
        assert goal.target_state == {}
        assert goal.metrics == []
        assert goal.autonomy_level == 2
        assert goal.priority == 5
        assert goal.status == GoalStatus.ACTIVE
        assert isinstance(goal.created_at, datetime)
        assert isinstance(goal.updated_at, datetime)

    def test_goal_full_construction(self):
        """Test 2: Goal with all fields provided."""
        now = datetime.now()
        goal = Goal(
            id="g-test-1",
            name="Provider Reliability > 99%",
            description="Ensure provider uptime exceeds 99 percent",
            target_state={"reliability": 0.99},
            metrics=["uptime", "latency_p99"],
            autonomy_level=4,
            priority=1,
            status=GoalStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        assert goal.id == "g-test-1"
        assert goal.name == "Provider Reliability > 99%"
        assert goal.target_state["reliability"] == 0.99
        assert goal.autonomy_level == 4
        assert goal.priority == 1

    def test_goal_autonomy_level_bounds(self):
        """Test 3: Autonomy level is clamped to 0-5."""
        with pytest.raises(Exception):
            Goal(name="Bad", autonomy_level=6)
        with pytest.raises(Exception):
            Goal(name="Bad", autonomy_level=-1)

    def test_goal_priority_bounds(self):
        """Test 4: Priority is clamped to 1-10."""
        with pytest.raises(Exception):
            Goal(name="Bad", priority=0)
        with pytest.raises(Exception):
            Goal(name="Bad", priority=11)

    def test_goal_extra_forbid(self):
        """Test 5: Extra fields are rejected."""
        with pytest.raises(Exception):
            Goal(name="Test", unknown_field="nope")  # type: ignore


# ════════════════════════════════════════════════════════════════════
# 2. GoalStatus Transitions
# ════════════════════════════════════════════════════════════════════


class TestGoalStatus:
    """Tests for GoalStatus enum and transitions."""

    def test_status_enum_values(self):
        """Test 6: All status enum values are valid."""
        assert GoalStatus.ACTIVE.value == "active"
        assert GoalStatus.PAUSED.value == "paused"
        assert GoalStatus.COMPLETED.value == "completed"
        assert GoalStatus.FAILED.value == "failed"
        assert GoalStatus.ARCHIVED.value == "archived"

    def test_update_status_changes_timestamp(self):
        """Test 7: update_status() updates both status and timestamp."""
        goal = Goal(name="Status Test")
        old_updated = goal.updated_at

        goal.update_status(GoalStatus.COMPLETED)
        assert goal.status == GoalStatus.COMPLETED
        assert goal.updated_at >= old_updated

    def test_status_iterable(self):
        """Test 8: All statuses are in the enum."""
        statuses = list(GoalStatus)
        assert len(statuses) == 5


# ════════════════════════════════════════════════════════════════════
# 3. GoalTreeManager — CRUD
# ════════════════════════════════════════════════════════════════════


class TestGoalTreeManagerCRUD:
    """CRUD operations for goals via GoalTreeManager."""

    async def test_add_and_get_goal(self, manager):
        """Test 9: Add a goal and retrieve it by ID."""
        goal = Goal(name="Reliability Goal")
        await manager.add_goal(goal)

        retrieved = await manager.get_goal(goal.id)
        assert retrieved is not None
        assert retrieved.name == "Reliability Goal"
        assert retrieved.id == goal.id

    async def test_get_nonexistent_goal(self, manager):
        """Test 10: Retrieving a missing goal returns None."""
        result = await manager.get_goal("does-not-exist")
        assert result is None

    async def test_add_goal_with_parent(self, manager):
        """Test 11: Add a goal as child of another goal."""
        parent = Goal(name="Parent Goal")
        child = Goal(name="Child Goal")
        await manager.add_goal(parent)
        await manager.add_goal(child, parent_id=parent.id)

        subgoals = await manager.get_subgoals(parent.id)
        assert len(subgoals) == 1
        assert subgoals[0].id == child.id

    async def test_add_goal_with_invalid_parent(self, manager):
        """Test 12: Adding a goal with missing parent raises error."""
        goal = Goal(name="Orphan")
        with pytest.raises(ValueError, match="not found"):
            await manager.add_goal(goal, parent_id="no-such-parent")

    async def test_update_goal(self, manager):
        """Test 13: Update a goal's properties."""
        goal = Goal(name="Original")
        await manager.add_goal(goal)

        goal.name = "Updated Name"
        goal.priority = 8
        await manager.update_goal(goal)

        retrieved = await manager.get_goal(goal.id)
        assert retrieved is not None
        assert retrieved.name == "Updated Name"
        assert retrieved.priority == 8

    async def test_delete_goal(self, manager):
        """Test 14: Delete a goal removes it from cache and DB."""
        goal = Goal(name="Delete Me")
        await manager.add_goal(goal)
        assert await manager.get_goal(goal.id) is not None

        await manager.delete_goal(goal.id)
        assert await manager.get_goal(goal.id) is None

    async def test_get_all_goals(self, manager):
        """Test 15: get_all_goals returns all known goals."""
        for i in range(5):
            g = Goal(name=f"Goal {i}")
            await manager.add_goal(g)

        all_goals = await manager.get_all_goals()
        assert len(all_goals) == 5

    async def test_get_ancestors(self, manager):
        """Test 16: get_ancestors returns root-first hierarchy."""
        root = Goal(name="Root")
        mid = Goal(name="Mid")
        leaf = Goal(name="Leaf")
        await manager.add_goal(root)
        await manager.add_goal(mid, parent_id=root.id)
        await manager.add_goal(leaf, parent_id=mid.id)

        ancestors = await manager.get_ancestors(leaf.id)
        assert len(ancestors) == 2
        assert ancestors[0].id == root.id  # root-first
        assert ancestors[1].id == mid.id


# ════════════════════════════════════════════════════════════════════
# 4. Goal Tree Hierarchy
# ════════════════════════════════════════════════════════════════════


class TestGoalTree:
    """GoalTree snapshot generation."""

    async def test_get_goal_tree_basic(self, manager):
        """Test 17: get_goal_tree returns a tree with root and children."""
        root = Goal(name="Root")
        child = Goal(name="Child")
        await manager.add_goal(root)
        await manager.add_goal(child, parent_id=root.id)

        tree = await manager.get_goal_tree(root.id)
        assert isinstance(tree, GoalTree)
        assert tree.root_goal_id == root.id
        assert root.id in tree.children
        assert child.id in tree.children[root.id]
        assert len(tree.children) == 2  # root + child each get an entry

    async def test_get_goal_tree_deep(self, manager):
        """Test 18: Deep nesting is properly captured."""
        ids = []
        prev_id = None
        for i in range(5):
            g = Goal(name=f"Level {i}")
            await manager.add_goal(g, parent_id=prev_id)
            ids.append(g.id)
            prev_id = g.id

        tree = await manager.get_goal_tree(ids[0])
        assert tree.root_goal_id == ids[0]
        # All 5 nodes should appear in children map
        assert len(tree.children) == 5

        # Chain: 0→1→2→3→4
        for i in range(4):
            assert ids[i + 1] in tree.children[ids[i]]

    async def test_get_goal_tree_nonexistent(self, manager):
        """Test 19: Requesting tree for missing goal raises error."""
        with pytest.raises(ValueError, match="not found"):
            await manager.get_goal_tree("ghost")


# ════════════════════════════════════════════════════════════════════
# 5. Goal Progress Evaluation
# ════════════════════════════════════════════════════════════════════


class TestGoalProgress:
    """Evidence-based progress evaluation."""

    async def test_progress_no_metrics_no_evidence(self, manager):
        """Test 20: Goal with no metrics returns 0.0."""
        goal = Goal(name="Empty")
        await manager.add_goal(goal)

        score = await manager.evaluate_goal_progress(goal.id, [])
        assert score == 0.0

    async def test_progress_completed_goal(self, manager):
        """Test 21: COMPLETED goal returns 1.0."""
        goal = Goal(name="Done Ziel", status=GoalStatus.COMPLETED)
        await manager.add_goal(goal)

        score = await manager.evaluate_goal_progress(goal.id, [])
        assert score == 1.0

    async def test_progress_failed_goal(self, manager):
        """Test 22: FAILED goal returns 0.0."""
        goal = Goal(name="Failed", status=GoalStatus.FAILED)
        await manager.add_goal(goal)

        score = await manager.evaluate_goal_progress(goal.id, [])
        assert score == 0.0

    async def test_progress_partial_match(self, manager):
        """Test 23: Partially matched metrics produce partial score."""
        goal = Goal(
            name="Multi Metric",
            metrics=["uptime", "latency"],
            target_state={"reliability": 0.99},
        )
        await manager.add_goal(goal)

        evidence = [
            {"metric": "uptime", "value": 0.995},
            {"metric": "latency", "value": 42},
            # reliability not in evidence
        ]

        score = await manager.evaluate_goal_progress(goal.id, evidence)
        # 2 out of 3 matched (uptime, latency matched; reliability not)
        assert 0.6 < score < 0.7  # 2/3 ≈ 0.67

    async def test_progress_full_match(self, manager):
        """Test 24: All metrics matched returns 1.0 for root-only goal."""
        goal = Goal(
            name="Fully Met",
            metrics=["uptime"],
            target_state={"reliability": 0.99},
        )
        await manager.add_goal(goal)

        evidence = [
            {"metric": "uptime", "value": 0.995},
            {"key": "reliability", "value": 0.99},
        ]

        score = await manager.evaluate_goal_progress(goal.id, evidence)
        assert score == 1.0

    async def test_progress_with_children(self, manager):
        """Test 25: Progress includes weighted child scores."""
        root = Goal(name="Root", metrics=["overall"])
        child = Goal(name="Child", metrics=["sub_metric"])
        await manager.add_goal(root)
        await manager.add_goal(child, parent_id=root.id)

        evidence = [
            {"metric": "overall", "value": "ok"},
            # child's sub_metric is NOT in evidence
        ]

        score = await manager.evaluate_goal_progress(root.id, evidence)
        # root: 1/1 = 1.0, child: 0/1 = 0.0
        # weighted: 0.4*1.0 + 0.6*0.0 = 0.4
        assert score == 0.4

    async def test_progress_archived_goal(self, manager):
        """Test 26: ARCHIVED goal returns 0.0 regardless of evidence."""
        goal = Goal(
            name="Archived",
            metrics=["anything"],
            status=GoalStatus.ARCHIVED,
        )
        await manager.add_goal(goal)

        evidence = [{"metric": "anything", "value": "yes"}]
        score = await manager.evaluate_goal_progress(goal.id, evidence)
        assert score == 0.0

    async def test_progress_nonexistent_goal(self, manager):
        """Test 27: Evaluating a missing goal raises error."""
        with pytest.raises(ValueError, match="not found"):
            await manager.evaluate_goal_progress("phantom", [])


# ════════════════════════════════════════════════════════════════════
# 6. Persistence — Cross-session consistency
# ════════════════════════════════════════════════════════════════════


class TestGoalPersistence:
    """Verify data survives across manager instances (real persistence)."""

    async def test_data_survives_reload(self, db_path):
        """Test 28: Goals persist across different manager instances."""
        db1 = Database(db_path)
        await db1.initialize()
        mgr1 = GoalTreeManager(db1)

        goal = Goal(name="Persistent Goal", metrics=["m1"])
        await mgr1.add_goal(goal)

        # Create a second manager on the same DB
        db2 = Database(db_path)
        await db2.initialize()
        mgr2 = GoalTreeManager(db2)

        retrieved = await mgr2.get_goal(goal.id)
        assert retrieved is not None
        assert retrieved.name == "Persistent Goal"
        assert retrieved.metrics == ["m1"]

    async def test_hierarchy_survives_reload(self, db_path):
        """Test 29: Goal relationships persist across restarts."""
        db1 = Database(db_path)
        await db1.initialize()
        mgr1 = GoalTreeManager(db1)

        parent = Goal(name="Parent")
        child = Goal(name="Child")
        await mgr1.add_goal(parent)
        await mgr1.add_goal(child, parent_id=parent.id)

        # Reload
        db2 = Database(db_path)
        await db2.initialize()
        mgr2 = GoalTreeManager(db2)

        subgoals = await mgr2.get_subgoals(parent.id)
        assert len(subgoals) == 1
        assert subgoals[0].id == child.id

        tree = await mgr2.get_goal_tree(parent.id)
        assert child.id in tree.children[parent.id]

    async def test_delete_cascades(self, db_path):
        """Test 30: Deleting a goal removes orphaned relationships."""
        db = Database(db_path)
        await db.initialize()
        mgr = GoalTreeManager(db)

        parent = Goal(name="Parent")
        child = Goal(name="Child")
        await mgr.add_goal(parent)
        await mgr.add_goal(child, parent_id=parent.id)

        # Delete child
        await mgr.delete_goal(child.id)
        assert await mgr.get_goal(child.id) is None

        # Parent should have no subgoals
        subgoals = await mgr.get_subgoals(parent.id)
        assert len(subgoals) == 0

    async def test_re_add_goal_with_same_id(self, db):
        """Test 31: Adding a goal with same ID overwrites (idempotent)."""
        mgr = GoalTreeManager(db)
        g1 = Goal(id="fixed-id", name="First", priority=3)
        await mgr.add_goal(g1)

        g2 = Goal(id="fixed-id", name="Second", priority=8)
        await mgr.add_goal(g2)

        retrieved = await mgr.get_goal("fixed-id")
        assert retrieved is not None
        assert retrieved.name == "Second"
        assert retrieved.priority == 8
