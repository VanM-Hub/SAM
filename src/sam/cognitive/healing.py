"""
Sprint 24 – Fase 3: Predictive Self-Healing

Detects potential problems before they occur (pattern-based) and
executes preventive or corrective actions. Supports pluggable
healing strategies backed by execution graphs.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, ConfigDict
import structlog

if TYPE_CHECKING:
    from ..persistence.database import Database

logger = structlog.get_logger()


# ── Healing Strategy ────────────────────────────────────────────────


class HealingStrategy(str, Enum):
    """Strategy for a healing action.

    PREVENT  — Take proactive action to prevent a predicted failure.
    REPAIR   — Repair a detected issue.
    VERIFY   — Run diagnostic checks to confirm system health.
    LEARN    — Update internal models based on observed patterns.
    """

    PREVENT = "prevent"
    REPAIR = "repair"
    VERIFY = "verify"
    LEARN = "learn"


# ── Healing Action ─────────────────────────────────────────────────


class HealingAction(BaseModel):
    """A single healing action tied to a pattern trigger.

    Attributes:
        id: Unique action identifier (UUID hex).
        trigger: Pattern string that activates this action,
                 e.g. "pattern.provider_timeout", "evidence.workspace_corruption".
        strategy: Healing strategy to apply.
        action_graph: Serialised execution graph steps (list of dict steps).
        precondition: Optional Python-evaluable condition string.
        cooldown: Minimum seconds before this action can re-run (default 300 = 5 min).
        created_at: When this action was registered.
        updated_at: Last update timestamp.
        last_run_at: When this action was last executed (None if never).
        success_count: Number of successful runs.
        failure_count: Number of failed runs.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    trigger: str
    strategy: HealingStrategy = HealingStrategy.REPAIR
    action_graph: List[Dict[str, Any]] = Field(default_factory=list)
    precondition: Optional[str] = None
    cooldown: int = Field(default=300, ge=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_run_at: Optional[datetime] = None
    success_count: int = Field(default=0, ge=0)
    failure_count: int = Field(default=0, ge=0)

    def is_ready(self, now: Optional[datetime] = None) -> bool:
        """Check if cooldown period has elapsed since last run."""
        if self.last_run_at is None:
            return True
        now = now or datetime.now()
        elapsed = (now - self.last_run_at).total_seconds()
        return elapsed >= self.cooldown

    def record_run(self, success: bool) -> None:
        """Update counters and timestamp after execution."""
        self.last_run_at = datetime.now()
        self.updated_at = self.last_run_at
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1


# ── Healing Result ─────────────────────────────────────────────────


class HealingResult(BaseModel):
    """Result of executing a healing action.

    Attributes:
        action_id: The action that was executed.
        success: Whether the healing succeeded.
        message: Human-readable result description.
        duration_ms: Execution time in milliseconds.
        details: Optional structured details.
    """

    model_config = ConfigDict(extra="forbid")

    action_id: str
    success: bool
    message: str = ""
    duration_ms: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)


# ── Built-in Pattern Definitions ────────────────────────────────────


# Well-known triggers
PATTERN_PROVIDER_TIMEOUT = "pattern.provider_timeout"
PATTERN_WORKSPACE_CORRUPTION = "evidence.workspace_corruption"
PATTERN_MEMORY_LEAK = "pattern.memory_leak"
PATTERN_ERROR_SPIKE = "pattern.error_spike"
PATTERN_LATENCY_INCREASE = "pattern.latency_increase"

ALL_BUILTIN_PATTERNS = {
    PATTERN_PROVIDER_TIMEOUT,
    PATTERN_WORKSPACE_CORRUPTION,
    PATTERN_MEMORY_LEAK,
    PATTERN_ERROR_SPIKE,
    PATTERN_LATENCY_INCREASE,
}


# ── Healing Manager ─────────────────────────────────────────────────


class HealingManager:
    """Manages healing actions: registration, pattern detection, execution.

    Usage:
        mgr = HealingManager(db)
        await mgr.register_pattern("pattern.provider_timeout", action)

        results = await mgr.detect_patterns(evidence_list)
        for action in results:
            result = await mgr.execute_healing(action)
    """

    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db
        self._actions: Dict[str, HealingAction] = {}  # trigger → action
        self._initialized = False

    async def _ensure_loaded(self) -> None:
        """Load all registered actions from DB."""
        if self._initialized:
            return
        self._initialized = True
        if not self._db:
            return

        rows = await self._db.fetch_all(
            "SELECT * FROM healing_actions ORDER BY created_at DESC"
        )
        for row in rows:
            action = self._row_to_action(row)
            self._actions[action.trigger] = action

    def _row_to_action(self, row: dict) -> HealingAction:
        return HealingAction(
            id=row.get("id", uuid.uuid4().hex[:12]),
            trigger=row.get("trigger", "unknown"),
            strategy=HealingStrategy(row.get("strategy", "repair")),
            action_graph=json.loads(row.get("action_graph", "[]")),
            precondition=row.get("precondition"),
            cooldown=row.get("cooldown", 300),
            created_at=datetime.fromisoformat(row["created_at"])
            if row.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"])
            if row.get("updated_at") else datetime.now(),
            last_run_at=datetime.fromisoformat(row["last_run_at"])
            if row.get("last_run_at") else None,
            success_count=row.get("success_count", 0),
            failure_count=row.get("failure_count", 0),
        )

    # ── Registration ──────────────────────────────────────────────

    async def register_pattern(
        self, pattern: str, action: HealingAction
    ) -> None:
        """Register a healing action for a pattern trigger.

        Overwrites any existing action for the same trigger.
        """
        await self._ensure_loaded()
        action.trigger = pattern
        action.updated_at = datetime.now()
        self._actions[pattern] = action

        if self._db:
            await self._db.execute(
                """INSERT OR REPLACE INTO healing_actions
                   (id, trigger, strategy, action_graph, precondition,
                    cooldown, created_at, updated_at, last_run_at,
                    success_count, failure_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    action.id,
                    pattern,
                    action.strategy.value,
                    json.dumps(action.action_graph),
                    action.precondition,
                    action.cooldown,
                    action.created_at.isoformat(),
                    action.updated_at.isoformat(),
                    action.last_run_at.isoformat()
                    if action.last_run_at else None,
                    action.success_count,
                    action.failure_count,
                ],
            )

        logger.info("Healing pattern registered", pattern=pattern, strategy=action.strategy.value)

    async def unregister_pattern(self, pattern: str) -> None:
        """Remove a registered healing pattern."""
        await self._ensure_loaded()
        self._actions.pop(pattern, None)
        if self._db:
            await self._db.execute(
                "DELETE FROM healing_actions WHERE trigger = ?",
                [pattern],
            )

    # ── Pattern Detection ─────────────────────────────────────────

    async def detect_patterns(
        self, evidence: List[Dict[str, Any]]
    ) -> List[HealingAction]:
        """Match evidence against registered patterns and return applicable actions.

        Simple matching logic:
          - If evidence dict has a 'pattern' key, that exact pattern is matched.
          - If evidence has a 'type' key, we try pattern.*type* and evidence.*type*.
          - All matched actions must pass their cooldown check.
        """
        await self._ensure_loaded()
        matched: List[HealingAction] = []

        for ev in evidence:
            trigger = ev.get("pattern") or ev.get("type")
            if not trigger:
                continue

            # Direct match
            if trigger in self._actions:
                action = self._actions[trigger]
                if action.is_ready() and self._check_precondition(action):
                    matched.append(action)
                continue

            # Try evidence.*trigger*
            evidence_key = f"evidence.{trigger}"
            if evidence_key in self._actions:
                action = self._actions[evidence_key]
                if action.is_ready() and self._check_precondition(action):
                    matched.append(action)

            # Try pattern.*trigger*
            pattern_key = f"pattern.{trigger}"
            if pattern_key in self._actions:
                action = self._actions[pattern_key]
                if action.is_ready() and self._check_precondition(action):
                    matched.append(action)

        # Deduplicate by action id
        seen: set = set()
        unique: List[HealingAction] = []
        for a in matched:
            if a.id not in seen:
                seen.add(a.id)
                unique.append(a)
        return unique

    def _check_precondition(self, action: HealingAction) -> bool:
        """Simplified precondition check — just returns True for now.

        In a production system this could eval a condition expression
        against the current system state.
        """
        if action.precondition is None:
            return True
        # Placeholder: skip precondition evaluation for now
        return True

    # ── Healing Execution ─────────────────────────────────────────

    async def execute_healing(self, action: HealingAction) -> HealingResult:
        """Execute a healing action.

        Simulates execution of each step in action_graph.
        In production this would dispatch to the workflow engine.
        """
        import time

        start = time.time()
        action_id = action.id

        try:
            await self._simulate_graph(action.action_graph)
            action.record_run(success=True)
            await self._persist_run(action)
            duration = int((time.time() - start) * 1000)
            logger.info("Healing action succeeded", action_id=action_id, duration_ms=duration)
            return HealingResult(
                action_id=action_id,
                success=True,
                message=f"Healing {action.strategy.value} completed for {action.trigger}",
                duration_ms=duration,
                details={"trigger": action.trigger, "strategy": action.strategy.value},
            )

        except Exception as e:
            action.record_run(success=False)
            await self._persist_run(action)
            duration = int((time.time() - start) * 1000)
            logger.error("Healing action failed", action_id=action_id, error=str(e))
            return HealingResult(
                action_id=action_id,
                success=False,
                message=str(e),
                duration_ms=duration,
                details={"trigger": action.trigger, "strategy": action.strategy.value},
            )

    async def _simulate_graph(self, graph: List[Dict[str, Any]]) -> None:
        """Simulate execution of a healing graph.

        In production, each step would be dispatched via the workflow engine.
        Raises on any step with "fail": true.
        """
        for step in graph:
            if step.get("fail"):
                raise RuntimeError(f"Step failed: {step.get('name', 'unknown')}")
        # Success — all steps passed

    async def _persist_run(self, action: HealingAction) -> None:
        """Persist updated counters and last_run_at to DB."""
        if not self._db:
            return
        await self._db.execute(
            """UPDATE healing_actions SET
               last_run_at = ?, success_count = ?, failure_count = ?,
               updated_at = ?
               WHERE id = ?""",
            [
                action.last_run_at.isoformat() if action.last_run_at else None,
                action.success_count,
                action.failure_count,
                action.updated_at.isoformat(),
                action.id,
            ],
        )

    # ── Query ─────────────────────────────────────────────────────

    async def get_actions_by_trigger(self, trigger: str) -> List[HealingAction]:
        """Return all actions registered for a specific trigger."""
        await self._ensure_loaded()
        action = self._actions.get(trigger)
        return [action] if action else []

    async def get_healing_history(self, limit: int = 50) -> List[HealingAction]:
        """Return all registered healing actions ordered by last run."""
        await self._ensure_loaded()
        sorted_actions = sorted(
            self._actions.values(),
            key=lambda a: a.last_run_at or datetime.min,
            reverse=True,
        )
        return sorted_actions[:limit]

    async def get_action_by_id(self, action_id: str) -> Optional[HealingAction]:
        """Retrieve a single action by ID."""
        await self._ensure_loaded()
        for action in self._actions.values():
            if action.id == action_id:
                return action
        return None


__all__ = [
    "HealingStrategy",
    "HealingAction",
    "HealingResult",
    "HealingManager",
    "PATTERN_PROVIDER_TIMEOUT",
    "PATTERN_WORKSPACE_CORRUPTION",
    "PATTERN_MEMORY_LEAK",
    "PATTERN_ERROR_SPIKE",
    "PATTERN_LATENCY_INCREASE",
    "ALL_BUILTIN_PATTERNS",
]
