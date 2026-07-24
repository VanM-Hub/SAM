"""
Sprint 24 – Fase 3: Graceful Degradation

When the system is uncertain, low on budget, or experiencing high
error rates, gracefully reduces autonomy level in stages rather
than failing abruptly. Recovers when conditions improve.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, ConfigDict
import structlog

from .autonomy import AutonomyLevel

if TYPE_CHECKING:
    from ..persistence.database import Database

logger = structlog.get_logger()


# ── Degradation Level ──────────────────────────────────────────────


class DegradationLevel(str, Enum):
    """Fallback autonomy level for graceful degradation.

    0  OBSERVE_ONLY          — Observe only, no actions permitted.
    1  RECOMMENDATION_ONLY   — May recommend actions, no execution.
    2  ASSISTED              — Human must confirm every action.
    3  SUPERVISED            — Minimal supervision, but may escalate.
    4  AUTONOMOUS            — Full autonomy (normal operation).
    """

    OBSERVE_ONLY = "observe_only"
    RECOMMENDATION_ONLY = "recommendation_only"
    ASSISTED = "assisted"
    SUPERVISED = "supervised"
    AUTONOMOUS = "autonomous"

    @property
    def numeric(self) -> int:
        """Return 0–4 numeric value."""
        mapping = {
            self.OBSERVE_ONLY: 0,
            self.RECOMMENDATION_ONLY: 1,
            self.ASSISTED: 2,
            self.SUPERVISED: 3,
            self.AUTONOMOUS: 4,
        }
        return mapping[self]

    def to_autonomy_level(self) -> AutonomyLevel:
        """Map to the closest AutonomyLevel for cross-reference."""
        mapping = {
            self.OBSERVE_ONLY: AutonomyLevel.OBSERVE_ONLY,
            self.RECOMMENDATION_ONLY: AutonomyLevel.RECOMMEND,
            self.ASSISTED: AutonomyLevel.EXECUTE_LOW_RISK,
            self.SUPERVISED: AutonomyLevel.EXECUTE_MEDIUM_RISK,
            self.AUTONOMOUS: AutonomyLevel.SUPERVISED_AUTONOMY,
        }
        return mapping[self]

    @staticmethod
    def from_numeric(value: int) -> "DegradationLevel":
        """Convert numeric 0–4 to DegradationLevel."""
        mapping = {
            0: DegradationLevel.OBSERVE_ONLY,
            1: DegradationLevel.RECOMMENDATION_ONLY,
            2: DegradationLevel.ASSISTED,
            3: DegradationLevel.SUPERVISED,
            4: DegradationLevel.AUTONOMOUS,
        }
        if value not in mapping:
            raise ValueError(f"Invalid degradation level numeric: {value}")
        return mapping[value]


# ── Degradation Record ─────────────────────────────────────────────


class DegradationRecord(BaseModel):
    """A single audit entry in the degradation history.

    Attributes:
        id: Unique record identifier.
        previous_level: The level before degradation/upgrade.
        new_level: The level after degradation/upgrade.
        reason: Why the change occurred.
        timestamp: When the change occurred.
        details: Additional context (budget state, error count, etc).
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    previous_level: DegradationLevel
    new_level: DegradationLevel
    reason: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)


# ── Degradation Manager ────────────────────────────────────────────


class DegradationManager:
    """Manages graceful degradation and recovery of autonomy levels.

    Uses health signals, budget state, error rate, and uncertainty
    metrics to recommend an appropriate degradation level.

    Usage:
        mgr = DegradationManager(db)
        current = await mgr.get_current_level()
        new_level = await mgr.degrade()          # drop one level
        recovered = await mgr.upgrade()          # rise one level
        recommended = await mgr.get_recommended_level(context)
    """

    def __init__(
        self,
        db: Optional[Database] = None,
    ) -> None:
        self._db = db
        self._current_level: DegradationLevel = DegradationLevel.AUTONOMOUS
        self._history: List[DegradationRecord] = []
        self._initialized = False

    async def _ensure_loaded(self) -> None:
        """Load current level + history from DB."""
        if self._initialized:
            return
        self._initialized = True
        if not self._db:
            return

        # Get the most recent record to determine current level
        last = await self._db.fetch_one(
            "SELECT * FROM degradation_history ORDER BY timestamp DESC LIMIT 1"
        )
        if last:
            self._current_level = DegradationLevel(last["new_level"])

        # Load recent history
        rows = await self._db.fetch_all(
            "SELECT * FROM degradation_history ORDER BY timestamp DESC LIMIT 100"
        )
        self._history = []
        for row in rows:
            self._history.append(
                DegradationRecord(
                    id=row["id"],
                    previous_level=DegradationLevel(row["previous_level"]),
                    new_level=DegradationLevel(row["new_level"]),
                    reason=row["reason"],
                    timestamp=datetime.fromisoformat(row["timestamp"])
                    if isinstance(row["timestamp"], str)
                    else row["timestamp"],
                    details=dict(row) if isinstance(row, dict) else {},
                )
            )

    # ── Level Management ──────────────────────────────────────────

    async def get_current_level(self) -> DegradationLevel:
        """Return the current degradation level."""
        await self._ensure_loaded()
        return self._current_level

    async def degrade(self) -> DegradationLevel:
        """Drop one degradation level (lower autonomy).

        Degradation chain:
            AUTONOMOUS (4) → SUPERVISED (3) → ASSISTED (2)
            → RECOMMENDATION_ONLY (1) → OBSERVE_ONLY (0)

        Returns:
            The new degradation level after degrading.
        """
        await self._ensure_loaded()
        current_val = self._current_level.numeric
        if current_val <= 0:
            logger.info("Already at minimum degradation level — cannot degrade further")
            return self._current_level

        new_numeric = current_val - 1
        new_level = DegradationLevel.from_numeric(new_numeric)
        previous = self._current_level
        self._current_level = new_level

        await self._record_change(previous, new_level, "degrade",
                                  "System degraded: uncertainty or budget exhausted")

        logger.info("System degraded", previous=previous.value, new=new_level.value)
        return self._current_level

    async def upgrade(self) -> DegradationLevel:
        """Rise one degradation level (more autonomy).

        Upgrade chain:
            OBSERVE_ONLY (0) → RECOMMENDATION_ONLY (1) → ASSISTED (2)
            → SUPERVISED (3) → AUTONOMOUS (4)

        Returns:
            The new degradation level after upgrading.
        """
        await self._ensure_loaded()
        current_val = self._current_level.numeric
        if current_val >= 4:
            logger.info("Already at maximum degradation level — cannot upgrade further")
            return self._current_level

        new_numeric = current_val + 1
        new_level = DegradationLevel.from_numeric(new_numeric)
        previous = self._current_level
        self._current_level = new_level

        await self._record_change(previous, new_level, "upgrade",
                                  "Automatic upgrade: system conditions have improved")

        logger.info("System upgraded", previous=previous.value, new=new_level.value)
        return self._current_level

    async def set_level(
        self, level: DegradationLevel, reason: str = "Manual override"
    ) -> DegradationLevel:
        """Explicitly set the degradation level to any value."""
        await self._ensure_loaded()
        previous = self._current_level
        self._current_level = level
        await self._record_change(previous, level, "manual_set", reason)
        return self._current_level

    # ── Recommendation ────────────────────────────────────────────

    async def get_recommended_level(
        self, context: Dict[str, Any]
    ) -> DegradationLevel:
        """Determine the recommended degradation level based on context.

        Context keys evaluated:
          - error_rate: float (0.0–1.0) — fraction of operations failing.
          - budget_remaining: Dict[str, int] — remaining cognitive budget.
          - health_score: float (0.0–1.0) — overall system health.
          - uncertainty: float (0.0–1.0) — system uncertainty level.
          - consecutive_failures: int — recent failures.

        Returns:
            The recommended degradation level.
        """
        await self._ensure_loaded()

        # Start from autonomous
        recommended_val = 4

        # 1. Error rate penalty
        error_rate = context.get("error_rate", 0.0)
        if error_rate > 0.4:
            recommended_val = 0  # → OBSERVE_ONLY
        elif error_rate > 0.25:
            recommended_val = 1  # → RECOMMENDATION_ONLY
        elif error_rate > 0.12:
            recommended_val = min(recommended_val, 3)  # → SUPERVISED at most
        elif error_rate > 0.05:
            recommended_val = min(recommended_val, 3)  # → SUPERVISED at most

        # 2. Budget exhaustion
        budget_remaining = context.get("budget_remaining", {})
        if budget_remaining:
            empty_budgets = sum(1 for v in budget_remaining.values() if v == 0)
            if empty_budgets >= 3:
                recommended_val = min(recommended_val, 1)  # → RECOMMENDATION_ONLY at most
            elif empty_budgets >= 2:
                recommended_val = min(recommended_val, 2)  # → ASSISTED at most
            elif empty_budgets >= 1:
                recommended_val = min(recommended_val, 3)  # → SUPERVISED at most

        # 3. Health score
        health_score = context.get("health_score", 1.0)
        if health_score < 0.3:
            recommended_val = min(recommended_val, 2)  # → ASSISTED at most
        elif health_score < 0.6:
            recommended_val = min(recommended_val, 3)  # → SUPERVISED at most

        # 4. Consecutive failures
        consecutive = context.get("consecutive_failures", 0)
        if consecutive > 10:
            recommended_val = 0  # → OBSERVE_ONLY
        elif consecutive > 5:
            recommended_val = min(recommended_val, 2)  # → ASSISTED at most
        elif consecutive > 2:
            recommended_val = min(recommended_val, 3)  # → SUPERVISED at most

        # Clamp
        recommended_val = max(0, min(4, recommended_val))
        return DegradationLevel.from_numeric(recommended_val)

    # ── History ────────────────────────────────────────────────────

    async def get_history(self, limit: int = 50) -> List[DegradationRecord]:
        """Return recent degradation/upgrade history."""
        await self._ensure_loaded()
        return sorted(
            self._history,
            key=lambda r: r.timestamp,
            reverse=True,
        )[:limit]

    # ── Internal ───────────────────────────────────────────────────

    async def _record_change(
        self,
        previous: DegradationLevel,
        new: DegradationLevel,
        action: str,
        reason: str,
    ) -> None:
        """Persist a degradation level change to DB and local history."""
        record = DegradationRecord(
            id=f"deg_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:4]}",
            previous_level=previous,
            new_level=new,
            reason=reason,
            timestamp=datetime.now(),
            details={"action": action},
        )
        self._history.append(record)

        if self._db:
            await self._db.execute(
                """INSERT INTO degradation_history
                   (id, previous_level, new_level, reason, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    record.id,
                    record.previous_level.value,
                    record.new_level.value,
                    record.reason,
                    record.timestamp.isoformat(),
                ],
            )


__all__ = [
    "DegradationLevel",
    "DegradationRecord",
    "DegradationManager",
]
