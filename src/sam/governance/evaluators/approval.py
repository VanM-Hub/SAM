"""
Approval Evaluator – Sprint 21 Fase 2

Checks whether the execution graph requires human or system approval
before it can run.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..evaluator import BaseEvaluator
from ..models import GovernanceDecision, GovernanceResult

if TYPE_CHECKING:
    from ...execution.graph import ExecutionGraph
    from ...runtime.context import ExecutionContext


class ApprovalEvaluator(BaseEvaluator):
    """Checks graph metadata for approval requirements.

    - If ``requires_approval`` is True in graph metadata → REQUIRE_APPROVAL
      with the specified approval_groups.
    - If graph references external systems tagged "sensitive" → REQUIRE_APPROVAL
    - Otherwise → ALLOW
    """

    @property
    def name(self) -> str:
        return "approval"

    async def _do_evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        return self._evaluate_sync(graph)

    def _evaluate_sync(self, graph: "ExecutionGraph") -> GovernanceResult:
        metadata = getattr(graph, "metadata", {}) or {}
        requires_approval = metadata.get("requires_approval", False)
        approval_groups = metadata.get("approval_groups", [])
        sensitive_targets = metadata.get("sensitive_targets", [])

        # Graph explicitly requires approval
        if requires_approval:
            groups = approval_groups if approval_groups else ["default-approvers"]
            return GovernanceResult.require_approval(
                reason="Graph requires explicit approval",
                approvals=groups,
            )

        # Sensitive targets detected
        if sensitive_targets:
            return GovernanceResult.require_approval(
                reason=f"Graph touches sensitive targets: {', '.join(sensitive_targets)}",
                approvals=["security-team"],
                warnings=[f"Sensitive: {', '.join(sensitive_targets)}"],
                metadata={"sensitive_targets": sensitive_targets},
            )

        return GovernanceResult.allowed(reason="No approval required")
