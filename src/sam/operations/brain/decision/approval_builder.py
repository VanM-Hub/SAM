"""
Approval Builder.

Builds ApprovalPreparation from DecisionPlan.
DTO only. Does NOT submit approvals.
"""

import uuid
from datetime import datetime
from typing import List

from .approval_preparation import ApprovalPreparation, ApprovalCandidate, ApprovalMetadata, ApprovalRequirement
from .planning import DecisionPlan, DecisionAlternative


class ApprovalBuilder:
    """Builds approval packages from plans."""

    def build(self, plan: DecisionPlan) -> ApprovalPreparation:
        """Build an approval preparation from a plan."""
        strategy = plan.strategy or {}
        requires_approval = strategy.get("requires_approval", False)

        metadata = ApprovalMetadata(
            plan_id=plan.plan_id,
            evaluation_id=plan.evaluation_id,
            strategy_approach=strategy.get("approach", "unknown"),
            requires_approval=requires_approval,
            created_at=datetime.now().timestamp(),
        )

        candidates = self._build_candidates(plan)
        requirements = self._build_requirements(plan)

        return ApprovalPreparation(
            preparation_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            metadata=metadata,
            candidates=candidates,
            requirements=requirements,
            summary=f"Approval: {len(candidates)} candidates, {self._satisfied_count(requirements)}/{len(requirements)} requirements met",
            ready_for_submission=all(r.satisfied for r in requirements),
        )

    def _build_candidates(self, plan: DecisionPlan) -> List[ApprovalCandidate]:
        candidates = []
        if plan.recommended:
            candidates.append(ApprovalCandidate(
                candidate_id=plan.recommended.alternative_id,
                runtime_id=plan.recommended.runtime_ids[0] if plan.recommended.runtime_ids else "",
                action_type=plan.recommended.action_type,
                priority=plan.recommended.priority,
                confidence=plan.recommended.confidence,
                requires_approval=self._needs_approval(plan),
            ))
        return candidates

    def _build_requirements(self, plan: DecisionPlan) -> List[ApprovalRequirement]:
        requirements = []

        # Plan completeness
        requirements.append(ApprovalRequirement(
            name="plan_complete", category="mandatory",
            satisfied=bool(plan.plan_id and plan.alternatives),
        ))

        # Strategy defined
        requirements.append(ApprovalRequirement(
            name="strategy_defined", category="mandatory",
            satisfied=plan.strategy is not None,
        ))

        # Constraints checked
        requirements.append(ApprovalRequirement(
            name="constraints_checked", category="mandatory",
            satisfied=plan.constraints is not None,
        ))

        # Recommended alternative
        requirements.append(ApprovalRequirement(
            name="recommended_alternative", category="mandatory",
            satisfied=plan.recommended is not None,
        ))

        # Summary available
        requirements.append(ApprovalRequirement(
            name="plan_summary", category="recommended",
            satisfied=bool(plan.summary),
        ))

        return requirements

    def _needs_approval(self, plan: DecisionPlan) -> bool:
        if plan.strategy:
            return plan.strategy.get("requires_approval", False)
        return True

    def _satisfied_count(self, requirements: List[ApprovalRequirement]) -> int:
        return sum(1 for r in requirements if r.satisfied)
