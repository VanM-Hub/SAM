"""Long-Term Objective — Sprint 27 Fase 1.

A high-level objective that aggregates one or more Strategic Goals
into a unified long-term aim. Provides aggregate progress tracking
across its constituent goals.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database


logger = structlog.get_logger()

OBJECTIVE_STATUSES = frozenset({"ACTIVE", "ACHIEVED", "ABANDONED"})


class LongTermObjective:
    """A long-term objective backed by one or more strategic goals.

    Tracks aggregate progress, milestones, and deadlines across
    the strategic goals that support it.
    """

    def __init__(
        self,
        id: str,
        description: str,
        strategic_goal_ids: Optional[List[str]] = None,
        timeline: Optional[Dict[str, Any]] = None,
        status: str = "ACTIVE",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if status not in OBJECTIVE_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. "
                f"Must be one of {sorted(OBJECTIVE_STATUSES)}"
            )
        self.id = id
        self.description = description
        self.strategic_goal_ids = strategic_goal_ids or []
        self.timeline = timeline or {}
        self.status = status
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "strategic_goal_ids": json.dumps(self.strategic_goal_ids),
            "timeline": json.dumps(self.timeline),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LongTermObjective:
        return cls(
            id=data["id"],
            description=data["description"],
            strategic_goal_ids=_parse_str_list(data.get("strategic_goal_ids")),
            timeline=_parse_timeline(data.get("timeline")),
            status=data.get("status", "ACTIVE"),
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
        )

    def __repr__(self) -> str:
        return (
            f"LongTermObjective(id={self.id!r}, "
            f"goals={len(self.strategic_goal_ids)}, "
            f"status={self.status!r})"
        )


def _parse_str_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v) for v in val]
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return [str(v) for v in parsed] if isinstance(parsed, list) else []
        except (ValueError, TypeError):
            return []
    return []


def _parse_timeline(val: Any) -> Dict[str, Any]:
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, dict) else {}
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


class ObjectiveManager:
    """Manages Long-Term Objectives — CRUD and aggregate progress."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.logger = logger.bind(component="ObjectiveManager")

    async def create_objective(self, objective: LongTermObjective) -> str:
        """Persist a new long-term objective."""
        d = objective.to_dict()
        await self.db.execute(
            """INSERT INTO long_term_objectives
               (id, description, strategic_goal_ids, timeline, status,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"], d["description"], d["strategic_goal_ids"],
                d["timeline"], d["status"],
                d["created_at"], d["updated_at"],
            ),
        )
        self.logger.info(
            "Long-term objective created",
            objective_id=objective.id,
            num_goals=len(objective.strategic_goal_ids),
        )
        return objective.id

    async def get_objective(
        self, objective_id: str
    ) -> Optional[LongTermObjective]:
        """Get an objective by ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM long_term_objectives WHERE id = ?", (objective_id,),
        )
        return LongTermObjective.from_dict(dict(row)) if row else None

    async def update_status(
        self, objective_id: str, status: str
    ) -> None:
        """Update objective status."""
        if status not in OBJECTIVE_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. "
                f"Must be one of {sorted(OBJECTIVE_STATUSES)}"
            )
        obj = await self._get_or_raise(objective_id)
        now = datetime.now(timezone.utc)
        await self.db.execute(
            "UPDATE long_term_objectives SET status = ?, updated_at = ? WHERE id = ?",
            (status, now.isoformat(), objective_id),
        )
        self.logger.info(
            "Objective status updated",
            objective_id=objective_id,
            old=obj.status,
            new=status,
        )

    async def add_strategic_goal(
        self, objective_id: str, goal_id: str
    ) -> None:
        """Link a strategic goal to an objective."""
        obj = await self._get_or_raise(objective_id)
        if goal_id in obj.strategic_goal_ids:
            return
        obj.strategic_goal_ids.append(goal_id)
        now = datetime.now(timezone.utc)
        await self.db.execute(
            "UPDATE long_term_objectives SET strategic_goal_ids = ?, updated_at = ? WHERE id = ?",
            (json.dumps(obj.strategic_goal_ids), now.isoformat(), objective_id),
        )

    async def remove_strategic_goal(
        self, objective_id: str, goal_id: str
    ) -> None:
        """Unlink a strategic goal from an objective."""
        obj = await self._get_or_raise(objective_id)
        obj.strategic_goal_ids = [g for g in obj.strategic_goal_ids if g != goal_id]
        now = datetime.now(timezone.utc)
        await self.db.execute(
            "UPDATE long_term_objectives SET strategic_goal_ids = ?, updated_at = ? WHERE id = ?",
            (json.dumps(obj.strategic_goal_ids), now.isoformat(), objective_id),
        )

    async def get_objective_progress(
        self, objective_id: str, goal_manager: "StrategicGoalManager | None" = None,
    ) -> float:
        """Calculate aggregate progress across all linked strategic goals.

        Returns 0.0–1.0. Falls back to mean of individual goal progresses
        via StrategicGoalManager.evaluate_progress if provided.
        """
        from sam.strategy.goal import StrategicGoalManager as SGM

        obj = await self._get_or_raise(objective_id)
        if not obj.strategic_goal_ids:
            return 0.0

        if goal_manager is not None:
            total = 0.0
            count = 0
            for gid in obj.strategic_goal_ids:
                progress = await goal_manager.evaluate_progress(gid)
                total += progress
                count += 1
            return total / count if count > 0 else 0.0

        return 0.0

    async def list_objectives(
        self, status: Optional[str] = None, limit: int = 50
    ) -> List[LongTermObjective]:
        """List objectives with optional status filter."""
        if status is not None and status not in OBJECTIVE_STATUSES:
            raise ValueError(f"Invalid status '{status}'")
        if status:
            rows = await self.db.fetch_all(
                """SELECT * FROM long_term_objectives
                   WHERE status = ? ORDER BY created_at DESC LIMIT ?""",
                (status, limit),
            )
        else:
            rows = await self.db.fetch_all(
                "SELECT * FROM long_term_objectives ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        return [LongTermObjective.from_dict(dict(r)) for r in rows]

    # ── Internal ────────────────────────────────────────────────

    async def _get_or_raise(self, objective_id: str) -> LongTermObjective:
        obj = await self.get_objective(objective_id)
        if obj is None:
            raise ValueError(f"Long-term objective not found: {objective_id}")
        return obj
