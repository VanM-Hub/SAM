"""Cognitive State Model & Manager — Sprint 29 Fase 1.

Defines CognitiveState (Pydantic) capturing runtime cognitive state:
intent, goal, health, confidence, focus, risk, autonomy, etc.
CognitiveStateManager manages current state and history.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


# ── Preset focus options ──────────────────────────────────────────

ALLOWED_FOCUS_VALUES = frozenset({
    "availability",
    "latency",
    "cost",
    "security",
    "balanced",
    "performance",
    "reliability",
})


class CognitiveState:
    """Immutable snapshot of SAM's cognitive runtime state.

    Attributes:
        id: Unique identifier (UUID).
        current_intent_id: Reference to the active Intent, if any.
        current_goal_id: Reference to the active Strategic Goal, if any.
        health: Overall system health 0.0–100.0 (derived from OperationalConfidence).
        confidence: Aggregate confidence 0.0–100.0.
        focus: Current attentional focus (e.g. "availability", "latency", "cost").
        risk: Current risk estimate 0.0–100.0.
        autonomy_level: Autonomy level 0 (fully manual) to 5 (fully autonomous).
        learning_objective: What SAM is currently trying to learn.
        current_strategy: Description of the active strategy.
        timestamp: When this state was captured.
        metadata: Extra context (source, trigger, etc.).
    """

    def __init__(
        self,
        id: str = "",
        current_intent_id: Optional[str] = None,
        current_goal_id: Optional[str] = None,
        health: float = 100.0,
        confidence: float = 100.0,
        focus: str = "balanced",
        risk: float = 0.0,
        autonomy_level: int = 2,
        learning_objective: str = "",
        current_strategy: str = "",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.id = id or f"cs_{uuid.uuid4().hex[:12]}"
        self.current_intent_id = current_intent_id
        self.current_goal_id = current_goal_id
        self.health = max(0.0, min(100.0, health))
        self.confidence = max(0.0, min(100.0, confidence))
        self.risk = max(0.0, min(100.0, risk))
        self.autonomy_level = max(0, min(5, autonomy_level))

        if focus not in ALLOWED_FOCUS_VALUES:
            focus = "balanced"
        self.focus = focus

        self.learning_objective = learning_objective
        self.current_strategy = current_strategy
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "current_intent_id": self.current_intent_id,
            "current_goal_id": self.current_goal_id,
            "health": self.health,
            "confidence": self.confidence,
            "focus": self.focus,
            "risk": self.risk,
            "autonomy_level": self.autonomy_level,
            "learning_objective": self.learning_objective,
            "current_strategy": self.current_strategy,
            "timestamp": self.timestamp.isoformat(),
            "metadata": json.dumps(self.metadata, default=str),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CognitiveState:
        return cls(
            id=data.get("id", ""),
            current_intent_id=data.get("current_intent_id"),
            current_goal_id=data.get("current_goal_id"),
            health=float(data.get("health", 100.0)),
            confidence=float(data.get("confidence", 100.0)),
            focus=data.get("focus", "balanced"),
            risk=float(data.get("risk", 0.0)),
            autonomy_level=int(data.get("autonomy_level", 2)),
            learning_objective=data.get("learning_objective", ""),
            current_strategy=data.get("current_strategy", ""),
            timestamp=_parse_dt(data.get("timestamp")),
            metadata=_parse_json(data.get("metadata", {})),
        )

    def __repr__(self) -> str:
        return (
            f"CognitiveState(id={self.id!r}, health={self.health}, "
            f"confidence={self.confidence}, focus={self.focus!r})"
        )


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


def _parse_json(val: Any) -> Any:
    if val is None:
        return {}
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (ValueError, TypeError):
            return val
    return val


# ── Cognitive State Manager ───────────────────────────────────────


class CognitiveStateManager:
    """Manages the current cognitive state and its history.

    Maintains:
      - current_state: the latest CognitiveState snapshot.
      - history: ordered list of past states.
    """

    def __init__(self) -> None:
        self._current_state: Optional[CognitiveState] = None
        self._history: List[CognitiveState] = []
        self.logger = logger.bind(component="CognitiveStateManager")

    async def get_current_state(self) -> CognitiveState:
        """Return the current cognitive state.

        If no state has been set yet, returns a default initial state.
        """
        if self._current_state is None:
            self._current_state = CognitiveState(
                id="cs_initial",
                health=100.0,
                confidence=100.0,
                focus="balanced",
                risk=0.0,
                autonomy_level=2,
            )
        return self._current_state

    async def update_state(self, updates: Dict[str, Any]) -> CognitiveState:
        """Create a new state snapshot by applying updates to the current state.

        The current state is frozen (immutable). A new CognitiveState is created
        with merged values, the previous state is archived to history.

        Args:
            updates: Dict of fields to change.

        Returns:
            The new CognitiveState.
        """
        current = await self.get_current_state()

        # Build new state from current + updates
        merged = {**current.to_dict(), **updates}
        merged["timestamp"] = datetime.now(timezone.utc)
        merged["id"] = f"cs_{uuid.uuid4().hex[:12]}"

        new_state = CognitiveState.from_dict(merged)

        # Archive previous state
        if self._current_state is not None:
            self._history.append(self._current_state)
            if len(self._history) > 10_000:
                self._history = self._history[-5000:]

        self._current_state = new_state
        self.logger.debug("Cognitive state updated", id=new_state.id, focus=new_state.focus)
        return new_state

    async def get_state_history(
        self,
        limit: int = 50,
    ) -> List[CognitiveState]:
        """Return recent state history, newest first."""
        history = list(self._history)
        history.reverse()
        return history[:limit]

    async def get_state_count(self) -> int:
        """Total number of historical states (excluding current)."""
        return len(self._history)
