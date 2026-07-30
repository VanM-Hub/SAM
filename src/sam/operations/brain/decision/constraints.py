"""
Decision Constraint Engine.

Checks constraints for decision execution.
Rule-based. Deterministic. Preview only.
"""

from typing import Dict, Any, List
from .evaluation import DecisionEvaluation, ReadinessLevel


class ConstraintEngine:
    """Checks decision constraints."""

    def check(self, evaluation: DecisionEvaluation) -> Dict[str, Any]:
        """Check all constraints."""
        blocked = False
        details = []

        # Policy constraint
        if evaluation.policy_result and not evaluation.policy_result.passed:
            details.append({"type": "policy", "blocked": True, "reason": "Policy violations exist"})
            blocked = True
        else:
            details.append({"type": "policy", "blocked": False})

        # Readiness constraint
        if evaluation.ready == ReadinessLevel.BLOCKED:
            details.append({"type": "readiness", "blocked": True, "reason": "Decision blocked by readiness check"})
            blocked = True
        else:
            details.append({"type": "readiness", "blocked": False})

        # Confidence constraint
        if evaluation.confidence in ("LOW",):
            details.append({"type": "confidence", "blocked": True, "reason": "Low confidence prevents execution"})
            blocked = True
        else:
            details.append({"type": "confidence", "blocked": False})

        # Summary
        return {
            "blocked": blocked,
            "can_proceed": not blocked,
            "details": details,
            "total_constraints": len(details),
            "blocked_count": sum(1 for d in details if d.get("blocked")),
        }
