"""
Sprint 24 – Fase 2: Autonomy Levels

Defines the autonomy level model for SAM's cognitive runtime.
Each level determines what actions the system may take without
human intervention — from pure observation to full autonomy.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ── Autonomy Level Enum ─────────────────────────────────────────────


class AutonomyLevel(str, Enum):
    """System autonomy level (0–5).

    0  OBSERVE_ONLY       — Observe only, no actions permitted.
    1  RECOMMEND          — May recommend actions, no execution.
    2  EXECUTE_LOW_RISK   — Execute low-risk actions only.
    3  EXECUTE_MEDIUM_RISK — Execute medium-risk or lower.
    4  SUPERVISED_AUTONOMY — Execute with minimal supervision.
    5  FULL_AUTONOMY      — Full execution without supervision.
    """

    OBSERVE_ONLY = "observe_only"
    RECOMMEND = "recommend"
    EXECUTE_LOW_RISK = "execute_low_risk"
    EXECUTE_MEDIUM_RISK = "execute_medium_risk"
    SUPERVISED_AUTONOMY = "supervised_autonomy"
    FULL_AUTONOMY = "full_autonomy"

    @property
    def numeric(self) -> int:
        """Return the numeric value 0–5."""
        mapping = {
            self.OBSERVE_ONLY: 0,
            self.RECOMMEND: 1,
            self.EXECUTE_LOW_RISK: 2,
            self.EXECUTE_MEDIUM_RISK: 3,
            self.SUPERVISED_AUTONOMY: 4,
            self.FULL_AUTONOMY: 5,
        }
        return mapping[self]

    def can_execute(self, action_risk_level: Optional[str] = None) -> bool:
        """Check if this autonomy level can execute the given risk level.

        Args:
            action_risk_level: One of 'low', 'medium', 'high', 'critical'.

        Rules:
            - OBSERVE_ONLY (0): never executes.
            - RECOMMEND (1): never executes.
            - EXECUTE_LOW_RISK (2): only 'low'.
            - EXECUTE_MEDIUM_RISK (3): 'low' or 'medium'.
            - SUPERVISED_AUTONOMY (4): any risk.
            - FULL_AUTONOMY (5): any risk.
        """
        if self.numeric <= 1:
            return False

        if self.numeric >= 4:
            return True

        if action_risk_level is None:
            return False

        risk_levels = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }
        risk_val = risk_levels.get(action_risk_level, 99)

        if self == AutonomyLevel.EXECUTE_LOW_RISK:
            return risk_val <= 1
        if self == AutonomyLevel.EXECUTE_MEDIUM_RISK:
            return risk_val <= 2

        return False  # defensive

    def requires_supervision(self) -> bool:
        """Return True if this level requires human supervision."""
        return self.numeric <= 3

    @staticmethod
    def from_numeric(value: int) -> AutonomyLevel:
        """Convert a numeric 0–5 back to an AutonomyLevel."""
        mapping = {
            0: AutonomyLevel.OBSERVE_ONLY,
            1: AutonomyLevel.RECOMMEND,
            2: AutonomyLevel.EXECUTE_LOW_RISK,
            3: AutonomyLevel.EXECUTE_MEDIUM_RISK,
            4: AutonomyLevel.SUPERVISED_AUTONOMY,
            5: AutonomyLevel.FULL_AUTONOMY,
        }
        if value not in mapping:
            raise ValueError(f"Invalid autonomy level numeric: {value}")
        return mapping[value]


# ── Autonomy Config Model ───────────────────────────────────────────


class AutonomyConfig(BaseModel):
    """Per-goal or system-wide autonomy configuration.

    Attributes:
        goal_id: The goal this config applies to (or '__system__' for global).
        min_autonomy_level: Minimum autonomy level permitted.
        max_autonomy_level: Maximum autonomy level permitted.
        override_rules: List of rule dicts for graph- or context-specific overrides.
        created_at: When this config was created.
        updated_at: When this config was last updated.
    """

    model_config = ConfigDict(extra="forbid")

    goal_id: str
    min_autonomy_level: AutonomyLevel = AutonomyLevel.OBSERVE_ONLY
    max_autonomy_level: AutonomyLevel = AutonomyLevel.FULL_AUTONOMY
    override_rules: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def effective_level(self) -> AutonomyLevel:
        """Return the effective autonomy level with override rules applied.

        For now, returns max_autonomy_level. Override rule evaluation
        will be implemented in a future sprint.
        """
        return self.max_autonomy_level

    def can_execute_action(self, action_risk_level: str) -> bool:
        """Check if the effective level permits execution at this risk level."""
        return self.effective_level().can_execute(action_risk_level)


__all__ = [
    "AutonomyLevel",
    "AutonomyConfig",
]
