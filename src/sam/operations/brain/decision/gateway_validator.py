"""
Gateway Validator.

Validates submission plans at the gateway boundary.
Rule-based. Deterministic.
"""

from typing import Dict, Any, List
from .submission_plan import ApprovalSubmissionPlan


class GatewayValidator:
    def validate(self, plan: ApprovalSubmissionPlan) -> Dict[str, Any]:
        errors = []; warnings = []

        if not plan.plan_id: errors.append("Missing plan ID")
        if not plan.envelope_id: errors.append("Missing envelope ID")
        if not plan.metadata: errors.append("Missing metadata")
        else:
            if not plan.metadata.submission_id: warnings.append("No submission ID")
        if not plan.stages: warnings.append("No stages defined")
        if not plan.references: warnings.append("No references")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings,
                "score": max(0, 1.0 - len(errors) * 0.3)}
