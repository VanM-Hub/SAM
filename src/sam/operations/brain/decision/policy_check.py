"""
Decision Policy Checker.

Checks if policies are satisfied for decision execution.
Rule-based. Deterministic.
"""

from .evaluation import EvaluationResult
from .package_context import DecisionContext


class PolicyChecker:
    """Checks decision policies."""

    def check(self, context: DecisionContext) -> EvaluationResult:
        violations = []; warnings = []

        # Priority policy
        if context.priority < 0:
            violations.append("Negative priority not allowed")

        # Confidence policy
        if context.confidence < 20.0:
            violations.append(f"Confidence {context.confidence} below minimum 20.0")
        elif context.confidence < 50.0:
            warnings.append(f"Low confidence: {context.confidence}")

        # Action type policy
        if not context.action_type or context.action_type == "unknown":
            warnings.append("No action type defined")

        # Runtime policy
        if context.runtime_ids and len(context.runtime_ids) > 5:
            warnings.append(f"High number of affected runtimes: {len(context.runtime_ids)}")

        # Justification policy
        if not context.has_justification:
            warnings.append("No justification — decision lacks explanation")

        # Readiness
        if not context.is_ready:
            violations.append("Context reports not ready")

        return EvaluationResult(passed=len(violations) == 0, score=max(0, 1 - len(violations)*0.3),
                                violations=violations, warnings=warnings)
