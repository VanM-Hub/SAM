"""
Sprint 24 – Goal & Goal Tree (Fase 1)

Defines the Goal model — the atomic unit of system intention:
what the system wants to achieve, how to measure progress,
and at what autonomy level.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ── Goal Status ─────────────────────────────────────────────────────


class GoalStatus(str, Enum):
    """Lifecycle status of a Goal."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


# ── Goal Model ──────────────────────────────────────────────────────


class Goal(BaseModel):
    """A discrete system goal — what we want to achieve.

    Goals are the atomic building blocks of the Goal Tree. Each goal
    captures a desired outcome, the metrics used to measure it, and
    the autonomy level at which the system may pursue it.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable name (e.g. \"Provider Reliability > 99%%\").
        description: Longer explanation of the goal.
        target_state: Dict describing the desired state / conditions.
        metrics: Metric key names used to gauge success.
        autonomy_level: 0 (manual) to 5 (fully autonomous); default 2.
        priority: 1 (highest) to 10 (lowest); default 5.
        status: Current lifecycle status.
        created_at: When this goal was created.
        updated_at: When this goal was last updated.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    description: str = ""
    target_state: Dict[str, Any] = Field(default_factory=dict)
    metrics: List[str] = Field(default_factory=list)
    autonomy_level: int = Field(default=2, ge=0, le=5)
    priority: int = Field(default=5, ge=1, le=10)
    status: GoalStatus = GoalStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update_status(self, new_status: GoalStatus) -> None:
        """Transition to a new status, updating updated_at."""
        self.status = new_status
        self.updated_at = datetime.now()


__all__ = [
    "GoalStatus",
    "Goal",
]
