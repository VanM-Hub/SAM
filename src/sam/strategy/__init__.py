"""SAM Strategy Package — Sprint 27 Fase 1.

Strategic Planning: Strategic Goals & Long-Term Objectives.
"""

from .goal import (
    StrategicGoal,
    StrategicGoalManager,
    GOAL_HORIZONS,
    GOAL_STATUSES,
)
from .objective import (
    LongTermObjective,
    ObjectiveManager,
    OBJECTIVE_STATUSES,
)

__all__ = [
    "StrategicGoal",
    "StrategicGoalManager",
    "GOAL_HORIZONS",
    "GOAL_STATUSES",
    "LongTermObjective",
    "ObjectiveManager",
    "OBJECTIVE_STATUSES",
]
