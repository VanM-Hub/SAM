"""
Decision Evaluator.

Evaluates DecisionContext and produces DecisionEvaluation.
Rule-based. Deterministic. No AI.
"""

import uuid
from datetime import datetime
from .evaluation import DecisionEvaluation, EvaluationResult, EvaluationReason, ReadinessLevel, ConfidenceLevel
from .package_context import DecisionContext
from .readiness import ReadinessChecker
from .policy_check import PolicyChecker
from .confidence import ConfidenceCalculator


class DecisionEvaluator:
    """Evaluates decision readiness from context."""

    def __init__(self) -> None:
        self._readiness = ReadinessChecker()
        self._policy = PolicyChecker()
        self._confidence = ConfidenceCalculator()

    def evaluate(self, context: DecisionContext) -> DecisionEvaluation:
        """Evaluate a DecisionContext."""
        # Policy check
        policy_result = self._policy.check(context)

        # Readiness check
        readiness_result = self._readiness.check(context)

        # Calculate confidence
        confidence = self._confidence.calculate(context, readiness_result, policy_result)

        # Determine overall readiness
        if policy_result.passed and readiness_result.passed:
            overall = EvaluationResult(passed=True, score=1.0)
            ready = ReadinessLevel.READY
        elif not policy_result.passed:
            overall = EvaluationResult(passed=False, score=0.0, violations=policy_result.violations)
            ready = ReadinessLevel.BLOCKED
        else:
            overall = EvaluationResult(passed=False, score=readiness_result.score)
            ready = ReadinessLevel.PARTIAL

        # Build reasons
        reasons = [
            EvaluationReason(primary="Policy evaluation", details=policy_result.violations + policy_result.warnings),
            EvaluationReason(primary="Readiness evaluation", details=readiness_result.violations + readiness_result.warnings),
        ]

        return DecisionEvaluation(
            evaluation_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            context_id=context.context_id,
            ready=ready,
            confidence=confidence,
            policy_result=policy_result,
            readiness_result=readiness_result,
            overall_result=overall,
            reasons=reasons,
        )
