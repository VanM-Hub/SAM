"""Attention Manager — Sprint 29 Fase 2.

Determines the primary runtime focus for SAM based on system state,
operational confidence, health metrics, and context. Focus influences
decisions in Self-Healing, Autotuning, and Evolution.
"""

from __future__ import annotations

import enum
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.cognition.state import CognitiveStateManager
from sam.cognition.memory import WorkingMemoryManager

logger = structlog.get_logger()


# ── Focus Area Enum ───────────────────────────────────────────────


class FocusArea(str, enum.Enum):
    AVAILABILITY = "availability"
    LATENCY = "latency"
    COST = "cost"
    SECURITY = "security"
    FEATURES = "features"
    BALANCED = "balanced"


# ── Default Weights ───────────────────────────────────────────────

DEFAULT_WEIGHTS: Dict[str, float] = {
    "availability": 0.25,
    "latency": 0.20,
    "cost": 0.20,
    "security": 0.15,
    "features": 0.20,
}

# Weights when focus is AVAILABILITY
AVAILABILITY_WEIGHTS: Dict[str, float] = {
    "availability": 0.60,
    "latency": 0.15,
    "cost": 0.10,
    "security": 0.10,
    "features": 0.05,
}

# Weights when focus is LATENCY
LATENCY_WEIGHTS: Dict[str, float] = {
    "availability": 0.20,
    "latency": 0.50,
    "cost": 0.10,
    "security": 0.10,
    "features": 0.10,
}

# Weights when focus is COST
COST_WEIGHTS: Dict[str, float] = {
    "availability": 0.15,
    "latency": 0.10,
    "cost": 0.55,
    "security": 0.10,
    "features": 0.10,
}

# Weights when focus is SECURITY
SECURITY_WEIGHTS: Dict[str, float] = {
    "availability": 0.15,
    "latency": 0.10,
    "cost": 0.10,
    "security": 0.55,
    "features": 0.10,
}

# Weights when focus is FEATURES
FEATURES_WEIGHTS: Dict[str, float] = {
    "availability": 0.15,
    "latency": 0.15,
    "cost": 0.10,
    "security": 0.10,
    "features": 0.50,
}

FOCUS_WEIGHT_MAP: Dict[FocusArea, Dict[str, float]] = {
    FocusArea.AVAILABILITY: AVAILABILITY_WEIGHTS,
    FocusArea.LATENCY: LATENCY_WEIGHTS,
    FocusArea.COST: COST_WEIGHTS,
    FocusArea.SECURITY: SECURITY_WEIGHTS,
    FocusArea.FEATURES: FEATURES_WEIGHTS,
    FocusArea.BALANCED: DEFAULT_WEIGHTS,
}


# ── AttentionProfile ──────────────────────────────────────────────


class AttentionProfile:
    """A snapshot of the current attentional focus.

    Attributes:
        id: Unique identifier.
        primary_focus: The main focus area.
        secondary_focus: A secondary focus area (optional).
        weights: Weight distribution across all areas.
        reason: Why this focus was chosen.
        confidence: Confidence in this focus decision (0.0–1.0).
        timestamp: When this profile was created.
    """

    def __init__(
        self,
        primary_focus: FocusArea = FocusArea.BALANCED,
        secondary_focus: Optional[FocusArea] = None,
        weights: Optional[Dict[str, float]] = None,
        reason: str = "",
        confidence: float = 1.0,
        id: str = "",
        timestamp: Optional[datetime] = None,
    ) -> None:
        self.id = id or f"ap_{uuid.uuid4().hex[:12]}"
        self.primary_focus = primary_focus
        self.secondary_focus = secondary_focus
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        self.reason = reason
        self.confidence = max(0.0, min(1.0, confidence))
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "primary_focus": self.primary_focus.value,
            "secondary_focus": self.secondary_focus.value if self.secondary_focus else None,
            "weights": json.dumps(self.weights, default=str),
            "reason": self.reason,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AttentionProfile:
        weights_raw = data.get("weights", {})
        if isinstance(weights_raw, str):
            try:
                weights_raw = json.loads(weights_raw)
            except (ValueError, TypeError):
                weights_raw = {}
        return cls(
            id=data.get("id", ""),
            primary_focus=FocusArea(data.get("primary_focus", "balanced")),
            secondary_focus=FocusArea(data["secondary_focus"]) if data.get("secondary_focus") else None,
            weights=weights_raw,
            reason=data.get("reason", ""),
            confidence=float(data.get("confidence", 1.0)),
            timestamp=_parse_dt(data.get("timestamp")),
        )

    def __repr__(self) -> str:
        return (
            f"AttentionProfile(id={self.id!r}, primary={self.primary_focus.value}, "
            f"confidence={self.confidence})"
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


# ── Attention Manager ─────────────────────────────────────────────


class AttentionManager:
    """Determines and manages the current attentional focus.

    Uses CognitiveState (health, confidence, risk, focus) and
    WorkingMemory (operational context) to decide the primary focus.
    """

    # Thresholds
    AVAILABILITY_CONFIDENCE_THRESHOLD = 70.0
    HEALTH_CRITICAL_THRESHOLD = 50.0
    HEALTH_DROP_THRESHOLD = 20.0  # percentage points drop
    CPU_HIGH_THRESHOLD = 80.0
    MEMORY_HIGH_THRESHOLD = 85.0
    COST_HIGH_THRESHOLD = 200.0  # arbitrary cost units

    def __init__(
        self,
        cognitive_state_manager: CognitiveStateManager,
        working_memory: WorkingMemoryManager,
    ) -> None:
        self._state_mgr = cognitive_state_manager
        self._wm = working_memory
        self._current_profile: Optional[AttentionProfile] = None
        self._history: List[AttentionProfile] = []
        self.logger = logger.bind(component="AttentionManager")

    async def determine_focus(self, context: Optional[Dict[str, Any]] = None) -> FocusArea:
        """Determine the primary focus area based on system state and context.

        Decision logic (first match wins):
          1. If Operational Confidence < threshold → AVAILABILITY.
          2. If health < critical threshold → AVAILABILITY.
          3. If health dropped significantly → AVAILABILITY.
          4. If CPU or memory are high and no failure → LATENCY.
          5. If operational cost is high and no critical issues → COST.
          6. Otherwise → BALANCED.

        Args:
            context: Optional dict with override keys like 'cpu_usage',
                     'memory_usage', 'operational_cost', etc.

        Returns:
            The selected FocusArea.
        """
        state = await self._state_mgr.get_current_state()
        ctx = context or {}

        # 1. Low operational confidence
        op_confidence = ctx.get("operational_confidence", state.confidence)
        if op_confidence < self.AVAILABILITY_CONFIDENCE_THRESHOLD:
            return FocusArea.AVAILABILITY

        # 2. Health critical
        health = ctx.get("health", state.health)
        if health < self.HEALTH_CRITICAL_THRESHOLD:
            return FocusArea.AVAILABILITY

        # 3. Health dropped significantly
        # Check state history for the previous health value
        prev_health = await self._get_previous_health(state.health)
        if prev_health is not None and (prev_health - state.health) >= self.HEALTH_DROP_THRESHOLD:
            return FocusArea.AVAILABILITY

        # 4. High CPU / memory and no critical failure
        cpu = ctx.get("cpu_usage", await self._get_wm_metric("cpu_usage"))
        mem = ctx.get("memory_usage", await self._get_wm_metric("memory_usage"))

        has_failure = ctx.get("has_active_failure", False)
        if not has_failure and (cpu is not None and cpu >= self.CPU_HIGH_THRESHOLD or
                                mem is not None and mem >= self.MEMORY_HIGH_THRESHOLD):
            return FocusArea.LATENCY

        # 5. High operational cost
        cost = ctx.get("operational_cost", await self._get_wm_metric("operational_cost"))
        if cost is not None and cost >= self.COST_HIGH_THRESHOLD:
            return FocusArea.COST

        # 6. Default
        return FocusArea.BALANCED

    async def apply_focus(self, focus: FocusArea, reason: str = "") -> AttentionProfile:
        """Create a new AttentionProfile with the given focus and archive the previous.

        Args:
            focus: The selected focus area.
            reason: Why this focus was chosen.

        Returns:
            The new AttentionProfile.
        """
        weights = FOCUS_WEIGHT_MAP.get(focus, DEFAULT_WEIGHTS)
        secondary = self._suggest_secondary(focus)
        confidence = await self._compute_confidence(focus)

        profile = AttentionProfile(
            primary_focus=focus,
            secondary_focus=secondary,
            weights=weights,
            reason=reason or f"Focus set to {focus.value}",
            confidence=confidence,
        )

        # Archive previous
        if self._current_profile is not None:
            self._history.append(self._current_profile)
            if len(self._history) > 10_000:
                self._history = self._history[-5000:]

        self._current_profile = profile

        # Also update the cognitive state's focus field
        await self._state_mgr.update_state({"focus": focus.value})

        self.logger.info(
            "Attention focus changed",
            primary=focus.value,
            secondary=secondary.value if secondary else None,
            confidence=confidence,
            reason=reason,
        )
        return profile

    async def determine_and_apply(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> AttentionProfile:
        """Convenience: determine focus then apply it."""
        focus = await self.determine_focus(context)
        reasons = []
        state = await self._state_mgr.get_current_state()

        op_conf = context.get("operational_confidence", state.confidence) if context else state.confidence
        health = context.get("health", state.health) if context else state.health
        cpu = context.get("cpu_usage") if context else None
        mem = context.get("memory_usage") if context else None
        cost = context.get("operational_cost") if context else None

        if focus == FocusArea.AVAILABILITY:
            if op_conf < self.AVAILABILITY_CONFIDENCE_THRESHOLD:
                reasons.append(f"Operational confidence {op_conf} < {self.AVAILABILITY_CONFIDENCE_THRESHOLD}")
            if health < self.HEALTH_CRITICAL_THRESHOLD:
                reasons.append(f"Health {health} < {self.HEALTH_CRITICAL_THRESHOLD}")
            if not reasons:
                reasons.append("Health degraded")
        elif focus == FocusArea.LATENCY:
            details = []
            if cpu is not None and cpu >= self.CPU_HIGH_THRESHOLD:
                details.append(f"CPU {cpu}%")
            if mem is not None and mem >= self.MEMORY_HIGH_THRESHOLD:
                details.append(f"Memory {mem}%")
            reasons.append(f"Resource pressure: {', '.join(details)}" if details else "Latency-sensitive")
        elif focus == FocusArea.COST:
            reasons.append(f"Operational cost {cost} >= threshold")
        else:
            reasons.append("Stable system — balanced focus")

        return await self.apply_focus(focus, "; ".join(reasons))

    async def get_current_profile(self) -> Optional[AttentionProfile]:
        """Return the current attention profile, or None if not set."""
        if self._current_profile is None:
            # Create a default BALANCED profile
            await self.apply_focus(
                FocusArea.BALANCED,
                "Initial default focus — no determination has run yet",
            )
        return self._current_profile

    async def update_weights(self, weights: Dict[str, float]) -> None:
        """Update the weight distribution of the current profile.

        Only modifies the current profile; does not change the focus area.
        """
        if self._current_profile is None:
            return
        # Normalize to sum 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        self._current_profile.weights = weights
        self.logger.debug("Attention weights updated", weights=weights)

    async def get_focus_history(self, limit: int = 50) -> List[AttentionProfile]:
        """Return recent attention profiles, newest first."""
        history = list(self._history)
        history.reverse()
        return history[:limit]

    async def get_profile_count(self) -> int:
        """Number of archived profiles (excluding current)."""
        return len(self._history)

    # ── Internal helpers ──────────────────────────────────────────

    async def _get_previous_health(self, current_health: float) -> Optional[float]:
        """Retrieve health from the previous cognitive state, if available."""
        history = await self._state_mgr.get_state_history(limit=1)
        if history:
            return history[0].health
        return None

    async def _get_wm_metric(self, key: str) -> Optional[float]:
        """Read a numeric metric from working memory."""
        val = await self._wm.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        return None

    async def _compute_confidence(self, focus: FocusArea) -> float:
        """Estimate confidence in the focus decision based on available data."""
        state = await self._state_mgr.get_current_state()
        # Base confidence from state confidence
        base = state.confidence / 100.0
        # If focus is BALANCED and state is healthy, high confidence
        if focus == FocusArea.BALANCED and state.health > 80:
            return min(1.0, base + 0.1)
        # If focus matches state focus, boost
        if focus.value == state.focus:
            return min(1.0, base + 0.05)
        return base

    @staticmethod
    def _suggest_secondary(focus: FocusArea) -> Optional[FocusArea]:
        """Suggest a secondary focus complementary to the primary."""
        suggestions = {
            FocusArea.AVAILABILITY: FocusArea.LATENCY,
            FocusArea.LATENCY: FocusArea.COST,
            FocusArea.COST: FocusArea.AVAILABILITY,
            FocusArea.SECURITY: FocusArea.AVAILABILITY,
            FocusArea.FEATURES: FocusArea.BALANCED,
            FocusArea.BALANCED: None,
        }
        return suggestions.get(focus)
