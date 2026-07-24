"""SAM Cognitive Runtime — Sprint 24

Goal, Goal Tree, Autonomy Levels, Cognitive Budget,
Predictive Self-Healing, and Graceful Degradation.
"""

from .goal import Goal, GoalStatus
from .goal_tree import GoalTree, GoalTreeManager
from .autonomy import AutonomyLevel, AutonomyConfig
from .budget import (
    CognitiveBudget,
    BudgetTracker,
    BUDGET_REASONING,
    BUDGET_PLANNING,
    BUDGET_REVISION,
    BUDGET_LEARNING,
    ALL_BUDGET_TYPES,
)
from .healing import (
    HealingStrategy,
    HealingAction,
    HealingResult,
    HealingManager,
    PATTERN_PROVIDER_TIMEOUT,
    PATTERN_WORKSPACE_CORRUPTION,
    PATTERN_MEMORY_LEAK,
    PATTERN_ERROR_SPIKE,
    PATTERN_LATENCY_INCREASE,
    ALL_BUILTIN_PATTERNS,
)
from .degradation import (
    DegradationLevel,
    DegradationRecord,
    DegradationManager,
)

__all__ = [
    # Fase 1
    "Goal",
    "GoalStatus",
    "GoalTree",
    "GoalTreeManager",
    # Fase 2
    "AutonomyLevel",
    "AutonomyConfig",
    "CognitiveBudget",
    "BudgetTracker",
    "BUDGET_REASONING",
    "BUDGET_PLANNING",
    "BUDGET_REVISION",
    "BUDGET_LEARNING",
    "ALL_BUDGET_TYPES",
    # Fase 3
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
    "DegradationLevel",
    "DegradationRecord",
    "DegradationManager",
]
