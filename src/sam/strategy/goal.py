"""Strategic Goal — Sprint 27 Fase 1.

Long-term strategic goals that sit above the Goal Tree (Cognitive Runtime).
Strategic goals have longer horizons (weeks/months) and serve as
reference points for all intents and goals beneath them.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database


logger = structlog.get_logger()

GOAL_HORIZONS = frozenset({"SHORT_TERM", "MEDIUM_TERM", "LONG_TERM"})
GOAL_STATUSES = frozenset({"ACTIVE", "PAUSED", "COMPLETED", "FAILED", "ARCHIVED"})


class StrategicGoal:
    """A high-level strategic goal with measurable target metrics.

    Strategic goals sit above Cognitive Goal Tree and drive long-term
    planning and resource allocation.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        horizon: str = "LONG_TERM",
        target_metrics: Optional[Dict[str, float]] = None,
        current_metrics: Optional[Dict[str, float]] = None,
        status: str = "ACTIVE",
        priority: int = 5,
        parent_goal_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if horizon not in GOAL_HORIZONS:
            raise ValueError(
                f"Invalid horizon '{horizon}'. "
                f"Must be one of {sorted(GOAL_HORIZONS)}"
            )
        if status not in GOAL_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. "
                f"Must be one of {sorted(GOAL_STATUSES)}"
            )
        if not (1 <= priority <= 10):
            raise ValueError(f"Priority must be between 1 and 10, got {priority}")
        self.id = id
        self.name = name
        self.description = description
        self.horizon = horizon
        self.target_metrics = target_metrics or {}
        self.current_metrics = current_metrics or {}
        self.status = status
        self.priority = priority
        self.parent_goal_id = parent_goal_id
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "horizon": self.horizon,
            "target_metrics": json.dumps(self.target_metrics),
            "current_metrics": json.dumps(self.current_metrics),
            "status": self.status,
            "priority": self.priority,
            "parent_goal_id": self.parent_goal_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StrategicGoal:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            horizon=data.get("horizon", "LONG_TERM"),
            target_metrics=_parse_metrics(data.get("target_metrics")),
            current_metrics=_parse_metrics(data.get("current_metrics")),
            status=data.get("status", "ACTIVE"),
            priority=data.get("priority", 5),
            parent_goal_id=data.get("parent_goal_id"),
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
        )

    def evaluate_progress(self) -> float:
        """Calculate progress toward target metrics.

        Returns a float 0.0–1.0 based on ratio of current to target values
        for each metric, averaged together.
        """
        if not self.target_metrics:
            return 0.0

        total_ratio = 0.0
        count = 0

        for key, target in self.target_metrics.items():
            if target == 0:
                continue
            current = self.current_metrics.get(key, 0.0)
            ratio = current / target
            # Clamp to [0.0, 1.0] — overshooting = 100%
            total_ratio += max(0.0, min(1.0, ratio))
            count += 1

        return total_ratio / count if count > 0 else 0.0

    def __repr__(self) -> str:
        return (
            f"StrategicGoal(id={self.id!r}, name={self.name!r}, "
            f"horizon={self.horizon!r}, status={self.status!r})"
        )


def _parse_metrics(val: Any) -> Dict[str, float]:
    if val is None:
        return {}
    if isinstance(val, dict):
        return {k: float(v) for k, v in val.items()}
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return {k: float(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}
        except (ValueError, TypeError):
            return {}
    return {}


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class StrategicGoalManager:
    """Manages strategic goal lifecycle — CRUD, hierarchy, progress evaluation."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.logger = logger.bind(component="StrategicGoalManager")

    async def create_goal(self, goal: StrategicGoal) -> str:
        """Persist a new strategic goal."""
        d = goal.to_dict()
        await self.db.execute(
            """INSERT INTO strategic_goals
               (id, name, description, horizon, target_metrics,
                current_metrics, status, priority, parent_goal_id,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"], d["name"], d["description"], d["horizon"],
                d["target_metrics"], d["current_metrics"],
                d["status"], d["priority"], d["parent_goal_id"],
                d["created_at"], d["updated_at"],
            ),
        )
        self.logger.info(
            "Strategic goal created",
            goal_id=goal.id,
            name=goal.name,
            horizon=goal.horizon,
        )
        return goal.id

    async def get_goal(self, goal_id: str) -> Optional[StrategicGoal]:
        """Get a strategic goal by ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM strategic_goals WHERE id = ?", (goal_id,),
        )
        return StrategicGoal.from_dict(dict(row)) if row else None

    async def update_metrics(
        self, goal_id: str, metrics: Dict[str, float]
    ) -> None:
        """Update current metrics for a goal, merging with existing."""
        goal = await self._get_or_raise(goal_id)
        merged = dict(goal.current_metrics)
        merged.update(metrics)
        now = datetime.now(timezone.utc)
        await self.db.execute(
            "UPDATE strategic_goals SET current_metrics = ?, updated_at = ? WHERE id = ?",
            (json.dumps(merged), now.isoformat(), goal_id),
        )
        self.logger.info("Strategic goal metrics updated", goal_id=goal_id)

    async def update_status(self, goal_id: str, status: str) -> None:
        """Update goal status."""
        if status not in GOAL_STATUSES:
            raise ValueError(f"Invalid status '{status}'")
        goal = await self._get_or_raise(goal_id)
        now = datetime.now(timezone.utc)
        await self.db.execute(
            "UPDATE strategic_goals SET status = ?, updated_at = ? WHERE id = ?",
            (status, now.isoformat(), goal_id),
        )
        self.logger.info(
            "Strategic goal status updated",
            goal_id=goal_id,
            old=goal.status,
            new=status,
        )

    async def get_goal_tree(self, goal_id: str) -> Dict[str, Any]:
        """Build a hierarchical tree of this goal and its descendants.

        Returns a dict with goal attributes and a 'children' list.
        """
        goal = await self._get_or_raise(goal_id)
        children = await self.db.fetch_all(
            "SELECT * FROM strategic_goals WHERE parent_goal_id = ? ORDER BY priority DESC",
            (goal_id,),
        )
        child_trees = []
        for child_row in children:
            child_tree = await self.get_goal_tree(child_row["id"])
            child_trees.append(child_tree)
        d = goal.to_dict()
        d["children"] = child_trees
        d["progress"] = goal.evaluate_progress()
        return d

    async def evaluate_progress(self, goal_id: str) -> float:
        """Evaluate goal progress (0.0–1.0) and consider children."""
        goal = await self._get_or_raise(goal_id)
        own = goal.evaluate_progress()
        children = await self.db.fetch_all(
            "SELECT * FROM strategic_goals WHERE parent_goal_id = ?",
            (goal_id,),
        )
        if not children:
            return own
        # Weighted average: own progress weighted 0.5, children 0.5
        child_total = 0.0
        for child_row in children:
            child_goal = StrategicGoal.from_dict(dict(child_row))
            child_total += child_goal.evaluate_progress()
        child_avg = child_total / len(children)
        return 0.5 * own + 0.5 * child_avg

    async def list_goals(
        self,
        status: Optional[str] = None,
        horizon: Optional[str] = None,
        limit: int = 50,
    ) -> List[StrategicGoal]:
        """List goals with optional filters."""
        conditions: List[str] = []
        params: List[Any] = []

        if status is not None:
            if status not in GOAL_STATUSES:
                raise ValueError(f"Invalid status '{status}'")
            conditions.append("status = ?")
            params.append(status)
        if horizon is not None:
            if horizon not in GOAL_HORIZONS:
                raise ValueError(f"Invalid horizon '{horizon}'")
            conditions.append("horizon = ?")
            params.append(horizon)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = await self.db.fetch_all(
            f"SELECT * FROM strategic_goals {where} ORDER BY priority DESC, created_at DESC LIMIT ?",
            (*params, limit),
        )
        return [StrategicGoal.from_dict(dict(r)) for r in rows]

    # ── Internal ────────────────────────────────────────────────

    async def _get_or_raise(self, goal_id: str) -> StrategicGoal:
        goal = await self.get_goal(goal_id)
        if goal is None:
            raise ValueError(f"Strategic goal not found: {goal_id}")
        return goal
