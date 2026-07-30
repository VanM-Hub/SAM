"""
Decision Strategy Builder.

Builds a decision strategy from evaluation.
Rule-based. Deterministic. No AI.
"""

from typing import Dict, Any
from .evaluation import DecisionEvaluation, ReadinessLevel


class StrategyBuilder:
    """Builds decision strategy from evaluation."""

    def build(self, evaluation: DecisionEvaluation) -> Dict[str, Any]:
        """Build strategy based on evaluation."""
        if evaluation.ready == ReadinessLevel.READY:
            approach = "direct_execution"
            urgency = "immediate" if evaluation.overall_result and evaluation.overall_result.score >= 0.8 else "normal"
        elif evaluation.ready == ReadinessLevel.PARTIAL:
            approach = "conditional_execution"
            urgency = "review_required"
        else:
            approach = "blocked_no_execution"
            urgency = "escalate"

        return {
            "approach": approach,
            "urgency": urgency,
            "confidence_level": evaluation.confidence,
            "readiness": evaluation.ready,
            "requires_approval": approach in ("conditional_execution", "blocked_no_execution"),
            "recommended_timing": "now" if approach == "direct_execution" else "after_review",
        }
