"""
Decision Readiness Checker.

Checks decision readiness based on multiple factors.
Rule-based. Deterministic.
"""

from .evaluation import EvaluationResult, ReadinessLevel
from .package_context import DecisionContext


class ReadinessChecker:
    """Checks decision readiness."""

    MIN_CONFIDENCE = 50.0
    MIN_EVIDENCE = 1
    MIN_PRIORITY = 0

    def check(self, context: DecisionContext) -> EvaluationResult:
        violations = []; warnings = []

        if context.confidence < self.MIN_CONFIDENCE:
            violations.append(f"Confidence too low: {context.confidence} < {self.MIN_CONFIDENCE}")

        if context.evidence_count < self.MIN_EVIDENCE:
            if not context.evidence_count:
                pass  # no explicit evidence count
            else:
                violations.append(f"Evidence too low: {context.evidence_count}")

        if not context.runtime_ids:
            warnings.append("No runtime IDs in context")

        if not context.action_type or context.action_type == "unknown":
            warnings.append("No action type determined")

        if not context.has_justification:
            warnings.append("No justification available")

        if context.priority < self.MIN_PRIORITY:
            warnings.append("Low priority")

        return EvaluationResult(passed=len(violations) == 0, score=max(0, 1 - len(violations)*0.3),
                                violations=violations, warnings=warnings)
