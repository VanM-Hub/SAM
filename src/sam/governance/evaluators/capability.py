"""
Capability Evaluator – Sprint 21 Fase 2

Evaluates whether required capabilities are available and healthy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable, Dict, Any, List

from ..evaluator import BaseEvaluator
from ..models import GovernanceDecision, GovernanceResult

if TYPE_CHECKING:
    from ...execution.graph import ExecutionGraph
    from ...runtime.context import ExecutionContext


class CapabilityEvaluator(BaseEvaluator):
    """Evaluates capability availability and health.

    Accepts optional callables for dependency injection:

    - ``get_capabilities`` () → Dict[str, str]
      Returns dict of {capability_name: status}, where status is one of
      "healthy", "degraded", "unhealthy", "missing".
    - ``get_required_capabilities`` (graph) → List[str]
      Returns list of capability names required by the graph.
      Default: reads ``required_capabilities`` from graph metadata.

    Decision logic:
    - Any required capability is "missing" → REJECT
    - Any required capability is "unhealthy" → REJECT
    - Any required capability is "degraded" → ALLOW_WITH_WARNING
    - All healthy → ALLOW
    """

    def __init__(
        self,
        *,
        get_capabilities: Optional[Callable[[], Dict[str, str]]] = None,
        get_required_capabilities: Optional[Callable[["ExecutionGraph"], List[str]]] = None,
    ) -> None:
        super().__init__()
        self._get_capabilities = get_capabilities
        self._get_required_capabilities = get_required_capabilities

    @property
    def name(self) -> str:
        return "capability"

    async def _do_evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        return self._evaluate_sync(graph)

    def _evaluate_sync(self, graph: "ExecutionGraph") -> GovernanceResult:
        # Determine required capabilities
        if self._get_required_capabilities:
            required = self._get_required_capabilities(graph)
        else:
            graph_meta = getattr(graph, "metadata", {}) or {}
            required = graph_meta.get("required_capabilities", [])

        if not required:
            return GovernanceResult.allowed(reason="No capability requirements")

        if not self._get_capabilities:
            # If no capability source, assume available (defer to runtime)
            return GovernanceResult.allowed(
                reason="Capability check skipped (no capability registry)",
                metadata={"required_capabilities": required},
            )

        capabilities = self._get_capabilities()
        missing: List[str] = []
        unhealthy: List[str] = []
        degraded: List[str] = []

        for cap_name in required:
            status = capabilities.get(cap_name, "missing")
            if status == "missing":
                missing.append(cap_name)
            elif status == "unhealthy":
                unhealthy.append(cap_name)
            elif status == "degraded":
                degraded.append(cap_name)

        metadata_bag: Dict[str, Any] = {
            "required_capabilities": required,
            "capability_statuses": capabilities,
        }

        # Missing → REJECT (cannot execute at all)
        if missing:
            return GovernanceResult.rejected(
                reason=f"Required capabilities missing: {', '.join(missing)}",
                metadata=metadata_bag,
            )

        # Unhealthy → REJECT (unreliable)
        if unhealthy:
            return GovernanceResult.rejected(
                reason=f"Required capabilities unhealthy: {', '.join(unhealthy)}",
                metadata=metadata_bag,
            )

        # Degraded → ALLOW_WITH_WARNING (may work, but reduced quality)
        if degraded:
            return GovernanceResult.allowed_with_warning(
                reason=f"Some capabilities degraded: {', '.join(degraded)}",
                warnings=[f"Degraded: {', '.join(degraded)}"],
                metadata=metadata_bag,
            )

        return GovernanceResult.allowed(
            reason="All required capabilities healthy",
            metadata=metadata_bag,
        )
