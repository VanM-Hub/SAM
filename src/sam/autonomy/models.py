"""Autonomy Models — Sprint 32.

Defines AutonomyLevel enum and shared config types.
"""

from __future__ import annotations

import enum


class AutonomyLevel(str, enum.Enum):
    """Five levels of operational autonomy.

    OBSERVE    — Watch only, no action.
    RECOMMEND  — Suggest actions, no execution.
    ASSIST     — Execute with human confirmation.
    SUPERVISE  — Execute with minimal supervision.
    AUTONOMOUS — Full execution without intervention.
    """
    OBSERVE = "observe"
    RECOMMEND = "recommend"
    ASSIST = "assist"
    SUPERVISE = "supervise"
    AUTONOMOUS = "autonomous"

    @property
    def numeric(self) -> int:
        return _NUMERIC_MAP[self]

    @classmethod
    def from_numeric(cls, value: int) -> AutonomyLevel:
        for level in cls:
            if level.numeric == value:
                return level
        return cls.OBSERVE

    def can_execute(self, risk: str = "low") -> bool:
        """Check if this level allows execution for a given risk."""
        if self == AutonomyLevel.OBSERVE:
            return False
        if self == AutonomyLevel.RECOMMEND:
            return False
        if self == AutonomyLevel.ASSIST and risk in ("high", "critical"):
            return False
        if self == AutonomyLevel.SUPERVISE and risk == "critical":
            return False
        return True


_NUMERIC_MAP = {
    AutonomyLevel.OBSERVE: 1,
    AutonomyLevel.RECOMMEND: 2,
    AutonomyLevel.ASSIST: 3,
    AutonomyLevel.SUPERVISE: 4,
    AutonomyLevel.AUTONOMOUS: 5,
}


class AutonomyConfig:
    """Configuration for autonomy controller behavior."""

    def __init__(
        self,
        default_level: AutonomyLevel = AutonomyLevel.SUPERVISE,
        min_confidence_for_autonomous: float = 80.0,
        max_risk_for_autonomous: str = "medium",
        escalation_on_unknown: bool = True,
    ) -> None:
        self.default_level = default_level
        self.min_confidence_for_autonomous = min_confidence_for_autonomous
        self.max_risk_for_autonomous = max_risk_for_autonomous
        self.escalation_on_unknown = escalation_on_unknown
