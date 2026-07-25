"""Optimizable Parameters — Sprint 28 Fase 1.

Defines the OptimizableParam model and ParamManager for
runtime-tunable system parameters with min/max bounds,
category grouping, and persistence.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database


logger = structlog.get_logger()

PARAM_CATEGORIES = frozenset({"RANKING", "SCHEDULER", "RETRY", "BUDGET", "TEMPLATE"})


class OptimizableParam:
    """A single tunable system parameter.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable key like 'ranking.weights.risk'.
        current_value: Current value (any JSON-serializable type).
        min_value: Minimum allowed value (or None if unbounded).
        max_value: Maximum allowed value (or None if unbounded).
        step: Step size for incremental adjustment (or None).
        category: One of RANKING, SCHEDULER, RETRY, BUDGET, TEMPLATE.
        description: Human-readable explanation.
        last_updated: UTC timestamp of last change.
    """

    def __init__(
        self,
        id: str,
        name: str,
        current_value: Any,
        min_value: Any = None,
        max_value: Any = None,
        step: Any = None,
        category: str = "RANKING",
        description: str = "",
        last_updated: Optional[datetime] = None,
    ) -> None:
        if category not in PARAM_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. "
                f"Must be one of {sorted(PARAM_CATEGORIES)}"
            )
        self.id = id
        self.name = name
        self.current_value = current_value
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.category = category
        self.description = description
        self.last_updated = last_updated or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "current_value": json.dumps(self.current_value),
            "min_value": json.dumps(self.min_value) if self.min_value is not None else None,
            "max_value": json.dumps(self.max_value) if self.max_value is not None else None,
            "step": json.dumps(self.step) if self.step is not None else None,
            "category": self.category,
            "description": self.description,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OptimizableParam:
        return cls(
            id=data["id"],
            name=data["name"],
            current_value=_parse_json(data["current_value"]),
            min_value=_parse_json(data.get("min_value")),
            max_value=_parse_json(data.get("max_value")),
            step=_parse_json(data.get("step")),
            category=data.get("category", "RANKING"),
            description=data.get("description", ""),
            last_updated=_parse_dt(data.get("last_updated")),
        )

    def __repr__(self) -> str:
        return (
            f"OptimizableParam(id={self.id!r}, name={self.name!r}, "
            f"value={self.current_value!r}, category={self.category})"
        )


def _parse_json(val: Any) -> Any:
    """Parse a JSON string back into a Python value."""
    if val is None:
        return None
    if isinstance(val, (str, bytes)):
        try:
            return json.loads(val)
        except (ValueError, TypeError):
            return val
    return val


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class ParamManager:
    """Manages optimizable parameters with DB persistence."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.logger = logger.bind(component="ParamManager")

    async def register_defaults(self) -> None:
        """Register standard system parameters with their defaults."""
        defaults = [
            OptimizableParam(
                id=self._id("param_ranking_risk"),
                name="ranking.weights.risk",
                current_value=0.3,
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                category="RANKING",
                description="Weight assigned to risk score in candidate ranking",
            ),
            OptimizableParam(
                id=self._id("param_ranking_cost"),
                name="ranking.weights.cost",
                current_value=0.2,
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                category="RANKING",
                description="Weight assigned to cost score in candidate ranking",
            ),
            OptimizableParam(
                id=self._id("param_ranking_success"),
                name="ranking.weights.success_probability",
                current_value=0.5,
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                category="RANKING",
                description="Weight assigned to success probability in ranking",
            ),
            OptimizableParam(
                id=self._id("param_scheduler_interval"),
                name="scheduler.interval_seconds",
                current_value=60,
                min_value=5,
                max_value=3600,
                step=5,
                category="SCHEDULER",
                description="Default polling interval in seconds for the scheduler",
            ),
            OptimizableParam(
                id=self._id("param_retry_max"),
                name="retry.max_attempts",
                current_value=3,
                min_value=1,
                max_value=10,
                step=1,
                category="RETRY",
                description="Maximum number of retry attempts for failed operations",
            ),
            OptimizableParam(
                id=self._id("param_retry_backoff"),
                name="retry.backoff_seconds",
                current_value=2.0,
                min_value=1.0,
                max_value=60.0,
                step=1.0,
                category="RETRY",
                description="Base backoff interval in seconds between retries",
            ),
            OptimizableParam(
                id=self._id("param_budget_max"),
                name="budget.max_execution_cost",
                current_value=1000,
                min_value=100,
                max_value=10000,
                step=100,
                category="BUDGET",
                description="Maximum execution cost budget per workflow",
            ),
            OptimizableParam(
                id=self._id("param_budget_autonomy"),
                name="budget.autonomy_threshold",
                current_value=0.8,
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                category="BUDGET",
                description="Budget threshold below which autonomy is restricted",
            ),
            OptimizableParam(
                id=self._id("param_template_complexity"),
                name="template.max_nodes",
                current_value=20,
                min_value=5,
                max_value=100,
                step=5,
                category="TEMPLATE",
                description="Maximum number of nodes in generated execution graphs",
            ),
        ]
        for param in defaults:
            existing = await self.get(param.name)
            if existing is None:
                await self._insert(param)
                self.logger.info("Default param registered", name=param.name)
            else:
                self.logger.debug("Default param already exists", name=param.name)

    async def get(self, param_name: str) -> Optional[OptimizableParam]:
        """Retrieve a parameter by its name."""
        row = await self.db.fetch_one(
            "SELECT * FROM optimizable_params WHERE name = ?",
            (param_name,),
        )
        if row is None:
            return None
        return OptimizableParam.from_dict(dict(row))

    async def set(self, param_name: str, value: Any) -> None:
        """Set a parameter's current value and bump last_updated."""
        existing = await self.get(param_name)
        if existing is None:
            raise ValueError(f"Parameter '{param_name}' not found")
        now = datetime.now(timezone.utc).isoformat()
        json_value = json.dumps(value)
        await self.db.execute(
            "UPDATE optimizable_params SET current_value = ?, last_updated = ? WHERE name = ?",
            (json_value, now, param_name),
        )
        self.logger.info("Parameter updated", name=param_name, value=value)

    async def list(
        self, category: Optional[str] = None
    ) -> List[OptimizableParam]:
        """List all parameters, optionally filtered by category."""
        if category is not None and category not in PARAM_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. "
                f"Must be one of {sorted(PARAM_CATEGORIES)}"
            )
        if category:
            rows = await self.db.fetch_all(
                "SELECT * FROM optimizable_params WHERE category = ? ORDER BY name",
                (category,),
            )
        else:
            rows = await self.db.fetch_all(
                "SELECT * FROM optimizable_params ORDER BY name"
            )
        return [OptimizableParam.from_dict(dict(r)) for r in rows]

    async def _insert(self, param: OptimizableParam) -> None:
        """Insert a new parameter (internal helper)."""
        d = param.to_dict()
        await self.db.execute(
            """INSERT OR REPLACE INTO optimizable_params
               (id, name, current_value, min_value, max_value, step,
                category, description, last_updated)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"], d["name"], d["current_value"],
                d["min_value"], d["max_value"], d["step"],
                d["category"], d["description"], d["last_updated"],
            ),
        )

    @staticmethod
    def _id(suffix: str) -> str:
        return f"opt-{suffix}"
