"""Operational Goal — tipe dan tujuan operasional SAM."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class GoalType(Enum):
    MISSION = 1
    STABILITY = 2
    RECOVERY = 3
    OPTIMIZATION = 4
    MAINTENANCE = 5
    LEARNING = 6
    MONITORING = 7
    CUSTOM = 8


@dataclass(frozen=True)
class OperationalGoal:
    """Sebuah tujuan operasional — apa yang perlu dicapai."""
    goal_id: str
    goal_type: GoalType
    title: str
    description: str
    priority: int                     # 1 (tertinggi) → 10
    deadline: Optional[float] = None  # unix timestamp
    constraints: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
