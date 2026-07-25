"""Goal Arbitration — Sprint 29 Fase 3.

Decides which goal (HEAL, OPTIMIZE, DEPLOY, SCALE, MONITOR, LEARN) 
should take priority when multiple goals compete, based on system state,
attention focus, and scoring.
"""

from __future__ import annotations

import enum
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.cognition.state import CognitiveStateManager
from sam.cognition.attention import AttentionManager, FocusArea

logger = structlog.get_logger()


# ── Goal Type ─────────────────────────────────────────────────────


class GoalType(str, enum.Enum):
    HEAL = "heal"
    OPTIMIZE = "optimize"
    DEPLOY = "deploy"
    SCALE = "scale"
    MONITOR = "monitor"
    LEARN = "learn"


# ── Goal Request ──────────────────────────────────────────────────


@dataclass
class GoalRequest:
    """A request to pursue a particular goal.

    Attributes:
        goal_type: Type of goal.
        priority: 1 (lowest) to 10 (highest).
        urgency: 0.0 (not urgent) to 1.0 (critical).
        resource_estimate: Estimated resource cost (arbitrary units).
        expected_duration: Estimated duration in seconds.
        confidence: Confidence this goal will succeed (0.0–1.0).
        context: Additional context dict.
    """
    goal_type: GoalType = GoalType.MONITOR
    priority: int = 5
    urgency: float = 0.5
    resource_estimate: float = 10.0
    expected_duration: int = 60
    confidence: float = 0.8
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_type": self.goal_type.value,
            "priority": self.priority,
            "urgency": self.urgency,
            "resource_estimate": self.resource_estimate,
            "expected_duration": self.expected_duration,
            "confidence": self.confidence,
            "context": json.dumps(self.context, default=str),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GoalRequest:
        ctx = data.get("context", {})
        if isinstance(ctx, str):
            try:
                ctx = json.loads(ctx)
            except (ValueError, TypeError):
                ctx = {}
        return cls(
            goal_type=GoalType(data.get("goal_type", "monitor")),
            priority=int(data.get("priority", 5)),
            urgency=float(data.get("urgency", 0.5)),
            resource_estimate=float(data.get("resource_estimate", 10.0)),
            expected_duration=int(data.get("expected_duration", 60)),
            confidence=float(data.get("confidence", 0.8)),
            context=ctx,
        )


# ── Arbitration Result ────────────────────────────────────────────


@dataclass
class ArbitrationResult:
    """Result of a goal arbitration.

    Attributes:
        selected_goal: The winning goal.
        reason: Why this goal was selected.
        confidence: Confidence in the decision (0.0–1.0).
        scores: Score per candidate goal type.
        runner_up: The second-best goal type, if any.
        timestamp: When arbitration occurred.
    """
    selected_goal: GoalType = GoalType.MONITOR
    reason: str = ""
    confidence: float = 0.5
    scores: Dict[str, float] = field(default_factory=dict)
    runner_up: Optional[GoalType] = None
    id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id or f"ar_{uuid.uuid4().hex[:12]}",
            "selected_goal": self.selected_goal.value,
            "reason": self.reason,
            "confidence": self.confidence,
            "scores": json.dumps(self.scores, default=str),
            "runner_up": self.runner_up.value if self.runner_up else None,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"ArbitrationResult(selected={self.selected_goal.value}, "
            f"confidence={self.confidence:.2f})"
        )


# ── Scoring Constants ─────────────────────────────────────────────

# Base priority per goal type (1-10)
GOAL_BASE_PRIORITY: Dict[GoalType, int] = {
    GoalType.HEAL: 8,
    GoalType.OPTIMIZE: 6,
    GoalType.DEPLOY: 4,
    GoalType.SCALE: 5,
    GoalType.MONITOR: 3,
    GoalType.LEARN: 2,
}

# Score coefficients
SCORE_PRIORITY_WEIGHT = 0.3
SCORE_URGENCY_WEIGHT = 0.4
SCORE_RESOURCE_WEIGHT = 0.3  # lower resource = higher score

# Thresholds
HEAL_CONFIDENCE_THRESHOLD = 70.0
OPTIMIZE_CONFIDENCE_THRESHOLD = 75.0
OPTIMIZE_HEALTH_THRESHOLD = 85.0
HEALTH_CRITICAL_THRESHOLD = 50.0
RESOURCE_MAX = 100.0


# ── Goal Arbitrator ───────────────────────────────────────────────


class GoalArbitrator:
    """Evaluates competing goals and selects the highest-priority one.

    Uses a weighted scoring model combined with context-aware
    adjustments from Cognitive State and Attention focus.
    """

    def __init__(
        self,
        cognitive_state_manager: CognitiveStateManager,
        attention_manager: AttentionManager,
    ) -> None:
        self._state_mgr = cognitive_state_manager
        self._attention = attention_manager
        self._current_goal: Optional[GoalType] = None
        self._history: List[ArbitrationResult] = []
        self.logger = logger.bind(component="GoalArbitrator")

    async def evaluate(self, goals: List[GoalRequest]) -> ArbitrationResult:
        """Evaluate a list of goal requests and select the best one.

        Steps:
          1. Compute base score for each goal.
          2. Apply context adjustments (state, focus, urgency).
          3. Select highest-scoring goal.
          4. Archive result.

        Args:
            goals: List of GoalRequest instances to evaluate.

        Returns:
            ArbitrationResult with the selected goal and reasoning.
        """
        if not goals:
            return ArbitrationResult(
                selected_goal=GoalType.MONITOR,
                reason="No goals provided — defaulting to MONITOR",
                confidence=1.0,
                scores={"monitor": 1.0},
            )

        state = await self._state_mgr.get_current_state()
        profile = await self._attention.get_current_profile()
        focus = profile.primary_focus if profile else FocusArea.BALANCED

        scores: Dict[str, float] = {}

        for goal in goals:
            base = self._compute_base_score(goal)
            adjusted = await self._apply_context_adjustments(
                goal, base, state, focus,
            )
            scores[goal.goal_type.value] = adjusted

        if not scores:
            return ArbitrationResult(
                selected_goal=GoalType.MONITOR,
                reason="No scores computed",
                confidence=0.0,
                scores={},
            )

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        selected_type = GoalType(ranked[0][0])
        selected_score = ranked[0][1]
        runner_up = GoalType(ranked[1][0]) if len(ranked) > 1 else None
        runner_score = ranked[1][1] if len(ranked) > 1 else 0

        # Reason
        reason = self._build_reason(
            selected_type, selected_score, focus, state,
        )

        # Confidence = normalized score difference
        score_diff = selected_score - runner_score
        confidence = min(1.0, max(0.1, score_diff / 10.0))
        confidence = min(1.0, confidence * (state.confidence / 100.0))

        result = ArbitrationResult(
            selected_goal=selected_type,
            reason=reason,
            confidence=round(confidence, 4),
            scores=scores,
            runner_up=runner_up,
        )

        self._current_goal = selected_type
        if result is not None:
            self._history.append(result)
            if len(self._history) > 10_000:
                self._history = self._history[-5000:]

        self.logger.info(
            "Goal arbitration complete",
            selected=selected_type.value,
            confidence=confidence,
            runner_up=runner_up.value if runner_up else None,
        )
        return result

    async def get_current_priority(self) -> Optional[GoalType]:
        """Return the currently prioritized goal."""
        return self._current_goal

    async def get_arbitration_history(
        self, limit: int = 50,
    ) -> List[ArbitrationResult]:
        """Return recent arbitration results, newest first."""
        history = list(self._history)
        history.reverse()
        return history[:limit]

    async def get_arbitration_count(self) -> int:
        """Number of arbitration results recorded."""
        return len(self._history)

    # ── Scoring ───────────────────────────────────────────────────

    @staticmethod
    def _compute_base_score(goal: GoalRequest) -> float:
        """Compute the base weighted score for a goal request."""
        pri = goal.priority * SCORE_PRIORITY_WEIGHT
        urg = goal.urgency * SCORE_URGENCY_WEIGHT

        # Resource: lower resource = higher score
        res_ratio = max(0.0, 1.0 - (goal.resource_estimate / RESOURCE_MAX))
        res = res_ratio * SCORE_RESOURCE_WEIGHT

        return pri + urg + res

    async def _apply_context_adjustments(
        self,
        goal: GoalRequest,
        base_score: float,
        state: "CognitiveState",
        focus: FocusArea,
    ) -> float:
        """Adjust the base score based on system context and focus.

        Returns adjusted score (in range ~0-20).
        """
        score = base_score

        # HEAL: boost if state needs healing
        if goal.goal_type == GoalType.HEAL:
            if state.confidence < HEAL_CONFIDENCE_THRESHOLD:
                score += 4.0
            if state.health < HEALTH_CRITICAL_THRESHOLD:
                score += 5.0
            if focus == FocusArea.AVAILABILITY:
                score += 3.0

        # OPTIMIZE: boost if healthy enough
        if goal.goal_type == GoalType.OPTIMIZE:
            if state.health >= OPTIMIZE_HEALTH_THRESHOLD:
                score += 2.0
            else:
                score -= 1.0  # Penalize if not healthy

        # DEPLOY: boost if focus is FEATURES
        if goal.goal_type == GoalType.DEPLOY:
            if focus == FocusArea.FEATURES:
                score += 2.0
            elif focus == FocusArea.AVAILABILITY:
                score -= 2.0  # Don't deploy during availability crisis

        # SCALE: boost if high load
        if goal.goal_type == GoalType.SCALE:
            if focus in (FocusArea.LATENCY, FocusArea.AVAILABILITY):
                score += 2.0

        # LEARN: boost if focus is BALANCED and healthy
        if goal.goal_type == GoalType.LEARN:
            if focus == FocusArea.BALANCED and state.health >= OPTIMIZE_HEALTH_THRESHOLD:
                score += 1.5
            elif focus != FocusArea.BALANCED:
                score -= 1.0  # Learning is low priority during crisis

        # Penalize low-confidence goals
        if goal.confidence < 0.3:
            score -= 2.0

        return max(0.0, score)

    @staticmethod
    def _build_reason(
        selected: GoalType,
        score: float,
        focus: FocusArea,
        state: "CognitiveState",
    ) -> str:
        """Build a human-readable reason for the arbitration decision."""
        parts = [f"Selected {selected.value} (score={score:.1f})"]
        parts.append(f"focus={focus.value}")
        parts.append(f"health={state.health:.0f}, confidence={state.confidence:.0f}")

        if selected == GoalType.HEAL:
            if state.confidence < HEAL_CONFIDENCE_THRESHOLD:
                parts.append("Healing needed: confidence below threshold")
            if state.health < HEALTH_CRITICAL_THRESHOLD:
                parts.append("Health critical")
        elif selected == GoalType.OPTIMIZE:
            parts.append("System healthy enough for optimization")
        elif selected == GoalType.DEPLOY:
            parts.append("Deployment requested or focus allows")
        elif selected == GoalType.MONITOR:
            parts.append("No pressing goals — monitoring")
        elif selected == GoalType.LEARN:
            parts.append("System stable — learning opportunity")

        return "; ".join(parts)
