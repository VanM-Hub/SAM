"""Strategic Plan Model — Sprint 27 Fase 2.

Holds a multi-phase strategic plan that decomposes a Strategic Goal
into ordered phases, each phase containing intents for execution.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database


logger = structlog.get_logger()

PLAN_STATUSES = frozenset({"PENDING", "ACTIVE", "COMPLETED", "FAILED", "PAUSED"})
INTENT_STATUSES = frozenset({"PENDING", "PLANNING", "APPROVED", "EXECUTING", "COMPLETED", "FAILED"})


class StrategicPlan:
    """A multi-phase strategic plan derived from a Strategic Goal.

    Each plan has an ordered list of phases. Each phase has a name,
    description, duration estimate, and a list of intents to execute.
    """

    def __init__(
        self,
        id: str,
        strategic_goal_id: str,
        name: str,
        description: str = "",
        phases: Optional[List[Dict[str, Any]]] = None,
        estimated_duration_days: int = 30,
        status: str = "PENDING",
        current_phase_index: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if status not in PLAN_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. "
                f"Must be one of {sorted(PLAN_STATUSES)}"
            )
        self.id = id
        self.strategic_goal_id = strategic_goal_id
        self.name = name
        self.description = description
        self.phases = phases or []
        self.estimated_duration_days = estimated_duration_days
        self.status = status
        self.current_phase_index = current_phase_index
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "strategic_goal_id": self.strategic_goal_id,
            "name": self.name,
            "description": self.description,
            "phases": json.dumps(self.phases),
            "estimated_duration_days": self.estimated_duration_days,
            "status": self.status,
            "current_phase_index": self.current_phase_index,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StrategicPlan:
        return cls(
            id=data["id"],
            strategic_goal_id=data["strategic_goal_id"],
            name=data["name"],
            description=data.get("description", ""),
            phases=_parse_phases(data.get("phases")),
            estimated_duration_days=data.get("estimated_duration_days", 30),
            status=data.get("status", "PENDING"),
            current_phase_index=data.get("current_phase_index", 0),
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
        )

    def __repr__(self) -> str:
        return (
            f"StrategicPlan(id={self.id!r}, name={self.name!r}, "
            f"status={self.status!r}, phase={self.current_phase_index})"
        )


def _parse_phases(val: Any) -> List[Dict[str, Any]]:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else []
        except (ValueError, TypeError):
            return []
    return []


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class StrategicPlanManager:
    """Manages strategic plan lifecycle — CRUD, phase advancement."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.logger = logger.bind(component="StrategicPlanManager")

    async def create_plan(self, plan: StrategicPlan) -> str:
        """Persist a new strategic plan."""
        d = plan.to_dict()
        await self.db.execute(
            """INSERT INTO strategic_plans
               (id, strategic_goal_id, name, description, phases,
                estimated_duration_days, status, current_phase_index,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"], d["strategic_goal_id"], d["name"], d["description"],
                d["phases"], d["estimated_duration_days"], d["status"],
                d["current_phase_index"], d["created_at"], d["updated_at"],
            ),
        )
        self.logger.info(
            "Strategic plan created",
            plan_id=plan.id,
            goal_id=plan.strategic_goal_id,
        )
        return plan.id

    async def get_plan(self, plan_id: str) -> Optional[StrategicPlan]:
        """Get a plan by ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM strategic_plans WHERE id = ?", (plan_id,),
        )
        return StrategicPlan.from_dict(dict(row)) if row else None

    async def update_status(self, plan_id: str, status: str) -> None:
        """Update plan status with validation."""
        if status not in PLAN_STATUSES:
            raise ValueError(f"Invalid status '{status}'")
        plan = await self._get_or_raise(plan_id)
        now = datetime.now(timezone.utc)
        await self.db.execute(
            "UPDATE strategic_plans SET status = ?, updated_at = ? WHERE id = ?",
            (status, now.isoformat(), plan_id),
        )
        self.logger.info("Plan status updated", plan_id=plan_id, old=plan.status, new=status)

    async def advance_phase(self, plan_id: str) -> int:
        """Advance to the next phase. Returns the new phase index."""
        plan = await self._get_or_raise(plan_id)
        next_idx = plan.current_phase_index + 1
        if next_idx >= len(plan.phases):
            raise ValueError(f"Plan '{plan_id}' has no more phases to advance")
        now = datetime.now(timezone.utc)
        await self.db.execute(
            "UPDATE strategic_plans SET current_phase_index = ?, updated_at = ? WHERE id = ?",
            (next_idx, now.isoformat(), plan_id),
        )
        self.logger.info("Plan advanced to next phase", plan_id=plan_id, phase=next_idx)
        return next_idx

    async def get_current_phase(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get the current phase dict, or None if plan has no phases."""
        plan = await self._get_or_raise(plan_id)
        if not plan.phases:
            return None
        idx = plan.current_phase_index
        if idx < 0 or idx >= len(plan.phases):
            return None
        return plan.phases[idx]

    async def list_plans(
        self,
        status: Optional[str] = None,
        goal_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[StrategicPlan]:
        """List plans with optional filters."""
        conditions: List[str] = []
        params: List[Any] = []
        if status is not None:
            if status not in PLAN_STATUSES:
                raise ValueError(f"Invalid status '{status}'")
            conditions.append("status = ?")
            params.append(status)
        if goal_id is not None:
            conditions.append("strategic_goal_id = ?")
            params.append(goal_id)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = await self.db.fetch_all(
            f"SELECT * FROM strategic_plans {where} ORDER BY created_at DESC LIMIT ?",
            (*params, limit),
        )
        return [StrategicPlan.from_dict(dict(r)) for r in rows]

    # ── Plan Intents ─────────────────────────────────────────────

    async def save_intent(
        self, plan_id: str, phase_index: int, intent_data: Dict[str, Any]
    ) -> str:
        """Persist an intent associated with a plan phase."""
        import uuid
        intent_id = intent_data.get("id", str(uuid.uuid4()))
        now = datetime.now(timezone.utc)
        await self.db.execute(
            """INSERT INTO plan_intents
               (id, plan_id, phase_index, intent_data, intent_type,
                target, description, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                intent_id,
                plan_id,
                phase_index,
                json.dumps(intent_data),
                intent_data.get("type", "CUSTOM"),
                intent_data.get("target", ""),
                intent_data.get("description", ""),
                "PENDING",
                now.isoformat(),
                now.isoformat(),
            ),
        )
        return intent_id

    async def get_phase_intents(
        self, plan_id: str, phase_index: int
    ) -> List[Dict[str, Any]]:
        """Get all intents for a given plan phase."""
        rows = await self.db.fetch_all(
            "SELECT * FROM plan_intents WHERE plan_id = ? AND phase_index = ? ORDER BY created_at",
            (plan_id, phase_index),
        )
        results = []
        for r in rows:
            intent = json.loads(r["intent_data"])
            intent["stored_id"] = r["id"]
            intent["status"] = r["status"]
            results.append(intent)
        return results

    # ── Internal ────────────────────────────────────────────────

    async def _get_or_raise(self, plan_id: str) -> StrategicPlan:
        plan = await self.get_plan(plan_id)
        if plan is None:
            raise ValueError(f"Strategic plan not found: {plan_id}")
        return plan
