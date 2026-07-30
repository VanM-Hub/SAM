"""
Submission Summary Builder.

Deterministic summary for submission plans.
"""

from typing import Dict, Any
from .submission_plan import ApprovalSubmissionPlan
from .approval_envelope import ApprovalRequestEnvelope


class SubmissionSummaryBuilder:
    def build(self, plan: ApprovalSubmissionPlan) -> Dict[str, Any]:
        return {
            "plan_id": plan.plan_id, "ready": plan.ready,
            "stages_completed": sum(1 for s in plan.stages if s.status == "completed"),
            "stages_pending": sum(1 for s in plan.stages if s.status == "pending"),
            "has_references": plan.references is not None,
            "has_metadata": plan.metadata is not None,
            "summary": plan.summary,
        }
