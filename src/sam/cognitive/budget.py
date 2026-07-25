"""
Sprint 24 – Fase 2: Cognitive Budget

Tracks and limits cognitive resource consumption across reasoning,
planning, revision, and learning cycles. Prevents runaway computation
by enforcing per-session and per-intent budgets.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, ConfigDict
import structlog

if TYPE_CHECKING:
    from ..persistence.database import Database

logger = structlog.get_logger()


# ── Budget Types ────────────────────────────────────────────────────

# Well-known budget type keys
BUDGET_REASONING = "reasoning_cycles"
BUDGET_PLANNING = "planning_attempts"
BUDGET_REVISION = "revision_count"
BUDGET_LEARNING = "learning_iterations"

ALL_BUDGET_TYPES = [
    BUDGET_REASONING,
    BUDGET_PLANNING,
    BUDGET_REVISION,
    BUDGET_LEARNING,
]


# ── Cognitive Budget Model ──────────────────────────────────────────


class CognitiveBudget(BaseModel):
    """Budget limits for cognitive operations.

    Defines the maximum number of cycles each cognitive operation
    may consume before being throttled.

    Attributes:
        id: Unique identifier (UUID).
        goal_id: The goal this budget applies to (or '__system__' for global).
        reasoning_cycles: Max reasoning cycles (default 5).
        planning_attempts: Max planning attempts per intent (default 3).
        revision_count: Max graph revisions (default 3).
        learning_iterations: Max learning iterations (default 10).
        created_at: When this budget was created.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    goal_id: str = "__system__"
    reasoning_cycles: int = Field(default=5, ge=1, le=100_000)
    planning_attempts: int = Field(default=3, ge=1, le=10_000)
    revision_count: int = Field(default=3, ge=0, le=10_000)
    learning_iterations: int = Field(default=10, ge=0, le=100_000)
    created_at: datetime = Field(default_factory=datetime.now)

    def get_limit(self, budget_type: str) -> int:
        """Return the max allowed count for a given budget type."""
        key = budget_type.replace("_cycles", "_count")  # normalize
        key = key.replace("_attempts", "_count")
        key = key.replace("_iterations", "_count")
        mapping: Dict[str, int] = {
            BUDGET_REASONING: self.reasoning_cycles,
            BUDGET_PLANNING: self.planning_attempts,
            BUDGET_REVISION: self.revision_count,
            BUDGET_LEARNING: self.learning_iterations,
        }
        return mapping.get(budget_type, 0)

    def to_consumption_model(self) -> CognitiveBudget:
        """Return a copy useful as a consumption tracker (limits = remaining)."""
        return self.model_copy(deep=True)


# ── Budget Tracker ──────────────────────────────────────────────────


class BudgetTracker:
    """Tracks budget consumption against a CognitiveBudget.

    Tracks how many cycles/attempts have been consumed for each
    budget type. Returns False from consume() when the budget is
    exhausted, preventing further cognitive work.

    Usage:
        tracker = BudgetTracker(budget, db, goal_id="g1")
        if await tracker.consume("reasoning_cycles"):
            # perform reasoning
        remaining = await tracker.get_remaining()
    """

    def __init__(
        self,
        budget: CognitiveBudget,
        db: Optional[Database] = None,
        tracker_id: Optional[str] = None,
        goal_id: str = "__system__",
    ) -> None:
        self._budget = budget
        self._db = db
        self._tracker_id = tracker_id or uuid.uuid4().hex[:12]
        self._goal_id = goal_id
        # In-memory consumption counters
        self._consumed: Dict[str, int] = {
            BUDGET_REASONING: 0,
            BUDGET_PLANNING: 0,
            BUDGET_REVISION: 0,
            BUDGET_LEARNING: 0,
        }
        self._persisted = False
        logger.debug(
            "BudgetTracker initialized",
            tracker_id=self._tracker_id,
            goal_id=goal_id,
        )

    # ── Properties ────────────────────────────────────────────────

    @property
    def budget(self) -> CognitiveBudget:
        return self._budget

    @property
    def tracker_id(self) -> str:
        return self._tracker_id

    @property
    def goal_id(self) -> str:
        return self._goal_id

    # ── Persistence ───────────────────────────────────────────────

    async def _ensure_table(self) -> None:
        """Create the budget_consumption table if it doesn't exist."""
        if self._db and not self._persisted:
            await self._db.execute(
                """CREATE TABLE IF NOT EXISTS budget_consumption (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    budget_type TEXT NOT NULL,
                    consumed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )"""
            )
            self._persisted = True

    async def _save_consumption(self, budget_type: str) -> None:
        """Persist consumption counter for this tracker + budget_type."""
        if not self._db:
            return
        await self._ensure_table()
        await self._db.execute(
            """INSERT OR REPLACE INTO budget_consumption
               (id, goal_id, budget_type, consumed, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            [
                f"{self._tracker_id}_{budget_type}",
                self._goal_id,
                budget_type,
                self._consumed[budget_type],
                datetime.now().isoformat(),
            ],
        )

    # ── Core API ──────────────────────────────────────────────────

    async def consume(self, budget_type: str, amount: int = 1) -> bool:
        """Consume budget for a given type.

        Args:
            budget_type: One of reasoning_cycles, planning_attempts,
                        revision_count, learning_iterations.
            amount: Units to consume (default 1).

        Returns:
            True if consumption was within budget (action permitted).
            False if budget is exhausted (action should be blocked).
        """
        if budget_type not in ALL_BUDGET_TYPES:
            logger.warning("Unknown budget type", budget_type=budget_type)
            return False

        current = self._consumed.get(budget_type, 0)
        limit = self._budget.get_limit(budget_type)

        if current + amount > limit:
            logger.warning(
                "Budget exhausted",
                budget_type=budget_type,
                consumed=current,
                limit=limit,
                requested=amount,
            )
            return False

        self._consumed[budget_type] = current + amount
        await self._save_consumption(budget_type)

        logger.debug(
            "Budget consumed",
            budget_type=budget_type,
            consumed=self._consumed[budget_type],
            limit=limit,
        )
        return True

    async def reset(self) -> None:
        """Reset all consumption counters for a new cycle."""
        for btype in ALL_BUDGET_TYPES:
            self._consumed[btype] = 0
            await self._save_consumption(btype)

        logger.info("Budget reset", tracker_id=self._tracker_id)

    async def get_remaining(self) -> Dict[str, int]:
        """Return remaining budget for each type."""
        remaining: Dict[str, int] = {}
        for btype in ALL_BUDGET_TYPES:
            limit = self._budget.get_limit(btype)
            consumed = self._consumed.get(btype, 0)
            remaining[btype] = max(0, limit - consumed)
        return remaining

    async def is_exhausted(self, budget_type: str) -> bool:
        """Check if a specific budget type is exhausted."""
        remaining = await self.get_remaining()
        return remaining.get(budget_type, 0) <= 0

    async def percent_used(self, budget_type: str) -> float:
        """Return 0.0–1.0 fraction of budget consumed."""
        limit = self._budget.get_limit(budget_type)
        if limit <= 0:
            return 0.0
        consumed = self._consumed.get(budget_type, 0)
        return min(consumed / limit, 1.0)


__all__ = [
    "CognitiveBudget",
    "BudgetTracker",
    "BUDGET_REASONING",
    "BUDGET_PLANNING",
    "BUDGET_REVISION",
    "BUDGET_LEARNING",
    "ALL_BUDGET_TYPES",
]
