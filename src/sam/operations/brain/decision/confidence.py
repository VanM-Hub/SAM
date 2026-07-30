"""
Decision Confidence Calculator.

Calc final confidence level from assessment, intent, evidence, history, and rule trace.
Rule-based. Deterministic.
"""

from .evaluation import EvaluationResult, ConfidenceLevel
from .package_context import DecisionContext


class ConfidenceCalculator:
    """Calculates final confidence level."""

    def calculate(
        self,
        context: DecisionContext,
        readiness_result: EvaluationResult,
        policy_result: EvaluationResult,
    ) -> str:
        """Calculate final confidence level."""
        score = context.confidence

        # Base adjustments
        if not context.has_justification:
            score -= 10.0

        if context.is_ready:
            score += 10.0

        if policy_result.passed:
            score += 5.0
        else:
            score -= 15.0

        if readiness_result.passed:
            score += 5.0
        else:
            score -= 10.0

        # Cap
        score = max(0, min(100, score))

        # Classify
        if score >= 85:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 70:
            return ConfidenceLevel.HIGH
        elif score >= 40:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
