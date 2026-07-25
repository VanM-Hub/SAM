"""
Sprint 24 – Goal Tree (Fase 1)

Defines the GoalTree structure and GoalTreeManager for managing
a hierarchical tree of Goals, evaluating progress against evidence,
and determining which Intent trees still align with the original goals.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, ConfigDict
import structlog

from .goal import Goal, GoalStatus

if TYPE_CHECKING:
    from ..persistence.database import Database

logger = structlog.get_logger()


# ── Goal Tree Model ─────────────────────────────────────────────────


class GoalTree(BaseModel):
    """A snapshot of the goal hierarchy rooted at a particular goal.

    Attributes:
        root_goal_id: The ID of the root goal for this tree view.
        children: Mapping from goal_id to a list of child goal_ids.
    """

    model_config = ConfigDict(extra="forbid")

    root_goal_id: str
    children: Dict[str, List[str]] = Field(default_factory=dict)


# ── Goal Tree Manager ───────────────────────────────────────────────


class GoalTreeManager:
    """Manages the Goal tree — CRUD, tree traversal, progress evaluation.

    Uses the Database layer for persistence, keeping the in-memory tree
    consistent with the stored state.
    """

    def __init__(self, db: Database) -> None:
        self._db = db
        self._cache: Dict[str, Goal] = {}
        self._children: Dict[str, List[str]] = {}  # parent_id → [child_id, ...]
        self._loaded = False

    # ── Internal helpers ──────────────────────────────────────────

    async def _ensure_loaded(self) -> None:
        """Lazy-load all goals and relationships from the database."""
        if self._loaded:
            return
        self._cache.clear()
        self._children.clear()

        rows = await self._db.fetch_all("SELECT * FROM goals")
        for row in rows:
            goal = Goal(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                target_state=json.loads(row["target_state"]),
                metrics=json.loads(row["metrics"]),
                autonomy_level=row["autonomy_level"],
                priority=row["priority"],
                status=GoalStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            self._cache[goal.id] = goal
            self._children.setdefault(goal.id, [])

        rel_rows = await self._db.fetch_all(
            "SELECT parent_id, child_id FROM goal_relationships"
        )
        for r in rel_rows:
            pid = r["parent_id"]
            cid = r["child_id"]
            self._children.setdefault(pid, []).append(cid)
            self._children.setdefault(cid, [])

        self._loaded = True

    async def _save_goal(self, goal: Goal) -> None:
        """Insert or replace a goal row."""
        await self._db.execute(
            """INSERT OR REPLACE INTO goals
               (id, name, description, target_state, metrics,
                autonomy_level, priority, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                goal.id,
                goal.name,
                goal.description,
                json.dumps(goal.target_state),
                json.dumps(goal.metrics),
                goal.autonomy_level,
                goal.priority,
                goal.status.value,
                goal.created_at.isoformat(),
                goal.updated_at.isoformat(),
            ],
        )

    async def _save_relationship(self, parent_id: str, child_id: str) -> None:
        """Insert a parent-child relationship."""
        await self._db.execute(
            "INSERT OR IGNORE INTO goal_relationships (parent_id, child_id) VALUES (?, ?)",
            [parent_id, child_id],
        )

    async def _remove_relationship(self, parent_id: str, child_id: str) -> None:
        """Remove a parent-child relationship."""
        await self._db.execute(
            "DELETE FROM goal_relationships WHERE parent_id = ? AND child_id = ?",
            [parent_id, child_id],
        )

    # ── Public API ────────────────────────────────────────────────

    async def add_goal(self, goal: Goal, parent_id: Optional[str] = None) -> None:
        """Add a new goal, optionally as a child of another goal.

        Args:
            goal: The Goal to add.
            parent_id: If set, the new goal becomes a child of this parent.
        """
        await self._ensure_loaded()

        if parent_id is not None and parent_id not in self._cache:
            raise ValueError(f"Parent goal '{parent_id}' not found")

        await self._save_goal(goal)
        self._cache[goal.id] = goal
        self._children.setdefault(goal.id, [])

        if parent_id:
            self._children.setdefault(parent_id, []).append(goal.id)
            await self._save_relationship(parent_id, goal.id)

        logger.info("Goal added", goal_id=goal.id, name=goal.name, parent_id=parent_id)

    async def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Retrieve a goal by its ID."""
        await self._ensure_loaded()
        return self._cache.get(goal_id)

    async def update_goal(self, goal: Goal) -> None:
        """Persist an updated goal to the database."""
        await self._ensure_loaded()
        goal.updated_at = datetime.now()
        self._cache[goal.id] = goal
        await self._save_goal(goal)
        logger.info("Goal updated", goal_id=goal.id)

    async def delete_goal(self, goal_id: str) -> None:
        """Remove a goal and all its relationships (but not children)."""
        await self._ensure_loaded()
        if goal_id not in self._cache:
            return

        # Remove all relationships where this goal is parent or child
        for pid in list(self._children.keys()):
            if goal_id in self._children[pid]:
                self._children[pid].remove(goal_id)
                await self._remove_relationship(pid, goal_id)

        # Remove from cache
        del self._cache[goal_id]
        self._children.pop(goal_id, None)

        # Delete from DB
        await self._db.execute(
            "DELETE FROM goal_relationships WHERE parent_id = ? OR child_id = ?",
            [goal_id, goal_id],
        )
        await self._db.execute("DELETE FROM goals WHERE id = ?", [goal_id])
        logger.info("Goal deleted", goal_id=goal_id)

    async def get_subgoals(self, goal_id: str) -> List[Goal]:
        """Get all direct children of a goal."""
        await self._ensure_loaded()
        child_ids = self._children.get(goal_id, [])
        return [self._cache[cid] for cid in child_ids if cid in self._cache]

    async def get_all_goals(self) -> List[Goal]:
        """Return all known goals."""
        await self._ensure_loaded()
        return list(self._cache.values())

    async def get_goal_tree(self, goal_id: str) -> GoalTree:
        """Build a GoalTree rooted at the given goal_id.

        The tree includes the root and all descendants reachable
        through the children mapping.

        Args:
            goal_id: The root goal ID.

        Returns:
            A GoalTree snapshot containing all descendant relationships.
        """
        await self._ensure_loaded()

        if goal_id not in self._cache:
            raise ValueError(f"Goal '{goal_id}' not found")

        children: Dict[str, List[str]] = {}
        stack = [goal_id]

        while stack:
            gid = stack.pop()
            if gid not in children:
                child_ids = self._children.get(gid, [])
                children[gid] = child_ids
                stack.extend(child_ids)

        return GoalTree(root_goal_id=goal_id, children=children)

    async def get_ancestors(self, goal_id: str) -> List[Goal]:
        """Get all ancestors of a goal (root-first order)."""
        await self._ensure_loaded()
        if goal_id not in self._cache:
            return []

        # Build reverse map: child_id → [parent_ids]
        reverse: Dict[str, List[str]] = {}
        for pid, children_list in self._children.items():
            for cid in children_list:
                reverse.setdefault(cid, []).append(pid)

        ancestors: List[Goal] = []
        visited: set = set()
        stack = list(reverse.get(goal_id, []))

        while stack:
            aid = stack.pop()
            if aid in visited or aid not in self._cache:
                continue
            visited.add(aid)
            ancestors.append(self._cache[aid])
            stack.extend(reverse.get(aid, []))

        # Reverse to get root-first order
        ancestors.reverse()
        return ancestors

    # ── Progress Evaluation ───────────────────────────────────────

    async def evaluate_goal_progress(
        self,
        goal_id: str,
        evidence: List[Dict[str, Any]],
    ) -> float:
        """Evaluate how much progress has been made toward a goal.

        Uses the goal's target_state and metrics against the provided
        evidence items. Returns a float 0.0 (no progress) to 1.0 (complete).

        Algorithm:
          1. Retrieve the goal and its subgoals.
          2. Score each subgoal based on metric overlap with evidence.
          3. Weighted average: root goal contributes 40%, children 60%.
          4. If target_state keys are present in evidence, check match.

        Args:
            goal_id: The goal to evaluate.
            evidence: List of dicts, each with at least "metric" or "key".

        Returns:
            A float between 0.0 and 1.0.
        """
        await self._ensure_loaded()

        goal = self._cache.get(goal_id)
        if goal is None:
            raise ValueError(f"Goal '{goal_id}' not found")

        if goal.status == GoalStatus.COMPLETED:
            return 1.0
        if goal.status in (GoalStatus.FAILED, GoalStatus.ARCHIVED):
            return 0.0

        # — Root goal self-score —
        self_score = self._score_goal_against_evidence(goal, evidence)

        # — Subgoal scores —
        child_ids = self._children.get(goal_id, [])
        if not child_ids:
            return self_score

        child_scores: List[float] = []
        for cid in child_ids:
            if cid in self._cache:
                child_score = await self.evaluate_goal_progress(cid, evidence)
                child_scores.append(child_score)

        if not child_scores:
            return self_score

        avg_child = sum(child_scores) / len(child_scores)

        # Weighted: 40% self, 60% children
        return 0.4 * self_score + 0.6 * avg_child

    def _score_goal_against_evidence(
        self,
        goal: Goal,
        evidence: List[Dict[str, Any]],
    ) -> float:
        """Compute a self-progress score (0.0-1.0) for a single goal."""
        if not goal.metrics and not goal.target_state:
            return 0.0

        matched = 0
        total = 0

        # Check metrics
        for metric in goal.metrics:
            total += 1
            for ev in evidence:
                ev_metric = ev.get("metric") or ev.get("name") or ""
                if ev_metric == metric:
                    matched += 1
                    break

        # Check target_state keys
        for key in goal.target_state:
            total += 1
            for ev in evidence:
                ev_key = ev.get("key") or ev.get("metric") or ""
                if ev_key == key:
                    matched += 1
                    break

        if total == 0:
            return 0.0

        return min(matched / total, 1.0)


__all__ = [
    "GoalTree",
    "GoalTreeManager",
]
