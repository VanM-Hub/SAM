"""SAM Evolution — Sprint 28.

Self-optimization, self-healing, and evolutionary architecture.
"""

from .params import OptimizableParam, ParamManager, PARAM_CATEGORIES
from .optimizer import SelfOptimizer, OptimizationSuggestion, OptimizationGoal
from .policy import EvolutionPolicy, EvolutionProposal, ProposalType, ProposalStatus, PolicyRule

__all__ = [
    "OptimizableParam",
    "ParamManager",
    "PARAM_CATEGORIES",
    "SelfOptimizer",
    "OptimizationSuggestion",
    "OptimizationGoal",
    "EvolutionPolicy",
    "EvolutionProposal",
    "ProposalType",
    "ProposalStatus",
    "PolicyRule",
]
