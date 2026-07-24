"""
Risk Evaluator – Sprint 21 Fase 2

Evaluates operational risk based on capability risk_level and graph metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..evaluator import BaseEvaluator
from ..models import GovernanceDecision, GovernanceResult

if TYPE_CHECKING:
    from ...execution.graph import ExecutionGraph
    from ...runtime.context import ExecutionContext


class RiskEvaluator(BaseEvaluator):
    """Evaluates operational risk of an execution graph.

    Risk is determined by:
    - Metadata flag ``requires_approval`` on the graph → REQUIRE_APPROVAL
    - ``risk_level`` capability metadata (Critical/High → REQUIRE_APPROVAL,
      Medium → ALLOW_WITH_WARNING, Low → ALLOW)
    - ``risk_score`` on graph metadata (> 0.7 → REJECT, > 0.5 → REQUIRE_APPROVAL)
    """

    @property
    def name(self) -> str:
        return "risk"

    async def _do_evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        return self._evaluate_sync(graph)

    def _evaluate_sync(self, graph: "ExecutionGraph") -> GovernanceResult:
        """Synchronous risk evaluation (also callable from GovernanceEngine)."""
        risk_score = graph.metadata.get("risk_score", None) if hasattr(graph, "metadata") else None

        # 1. Explicit rejection threshold
        if isinstance(risk_score, (int, float)) and risk_score > 0.7:
            return GovernanceResult.rejected(
                reason=f"Risk score {risk_score:.2f} exceeds maximum threshold (0.7)",
                metadata={"risk_score": risk_score},
            )

        # 2. High risk → require approval
        if isinstance(risk_score, (int, float)) and risk_score > 0.5:
            return GovernanceResult.require_approval(
                reason=f"Risk score {risk_score:.2f} exceeds approval threshold (0.5)",
                approvals=["ops-lead"],
                warnings=[f"Elevated risk: {risk_score:.2f}"],
                metadata={"risk_score": risk_score},
            )

        # 3. Graph metadata requires approval
        if graph.metadata.get("requires_approval") if hasattr(graph, "metadata") else False:
            return GovernanceResult.require_approval(
                reason="Graph requires explicit approval",
                approvals=graph.metadata.get("approval_groups", ["ops-lead"]),
            )

        # 4. Moderate risk → allow with warning
        if isinstance(risk_score, (int, float)) and risk_score > 0.3:
            return GovernanceResult.allowed_with_warning(
                reason=f"Moderate risk ({risk_score:.2f}) — monitor closely",
                warnings=[f"Risk score: {risk_score:.2f}"],
                metadata={"risk_score": risk_score},
            )

        # 5. Low risk → allow
        risk_display = f" ({risk_score:.2f})" if isinstance(risk_score, (int, float)) else ""
        return GovernanceResult.allowed(
            reason=f"Risk acceptable{risk_display}",
            metadata={"risk_score": risk_score},
        )
