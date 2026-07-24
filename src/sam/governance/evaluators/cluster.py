"""
Cluster Evaluator – Sprint 21 Fase 2

Evaluates cluster health and load before allowing graph execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable, Dict, Any

from ..evaluator import BaseEvaluator
from ..models import GovernanceDecision, GovernanceResult

if TYPE_CHECKING:
    from ...execution.graph import ExecutionGraph
    from ...runtime.context import ExecutionContext


class ClusterEvaluator(BaseEvaluator):
    """Evaluates cluster conditions: load, online node count, health.

    Accepts optional callables for dependency injection:

    - ``get_cluster_load`` () → float (0.0–100.0)
    - ``get_online_node_count`` () → int
    - ``get_minimum_online_nodes`` () → int (default 1)

    Thresholds:
    - Load > 90% → REJECT (cluster overloaded)
    - Load > 70% → WAIT (cluster under pressure)
    - Online nodes < minimum → WAIT (insufficient capacity)
    - Otherwise → ALLOW
    """

    def __init__(
        self,
        *,
        get_cluster_load: Optional[Callable[[], float]] = None,
        get_online_node_count: Optional[Callable[[], int]] = None,
        get_minimum_online_nodes: Optional[Callable[[], int]] = None,
        reject_load_threshold: float = 90.0,
        wait_load_threshold: float = 70.0,
    ) -> None:
        super().__init__()
        self._get_cluster_load = get_cluster_load
        self._get_online_node_count = get_online_node_count
        self._get_minimum_online_nodes = get_minimum_online_nodes
        self._reject_load_threshold = reject_load_threshold
        self._wait_load_threshold = wait_load_threshold

    @property
    def name(self) -> str:
        return "cluster"

    async def _do_evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        return self._evaluate_sync(graph)

    def _evaluate_sync(self, graph: "ExecutionGraph") -> GovernanceResult:
        metadata_bag: Dict[str, Any] = {}

        # 1. Check node count
        if self._get_online_node_count:
            online = self._get_online_node_count()
            minimum = self._get_minimum_online_nodes() if self._get_minimum_online_nodes else 1
            metadata_bag["online_nodes"] = online
            metadata_bag["minimum_nodes"] = minimum

            if online < minimum:
                return GovernanceResult.wait(
                    reason=f"Insufficient online nodes ({online}/{minimum})",
                    suggested_delay=30,
                    metadata=metadata_bag,
                )

        # 2. Check cluster load
        if self._get_cluster_load:
            load = self._get_cluster_load()
            metadata_bag["cluster_load"] = load

            if load > self._reject_load_threshold:
                return GovernanceResult.rejected(
                    reason=f"Cluster overloaded — load {load:.1f}% exceeds "
                           f"reject threshold ({self._reject_load_threshold}%)",
                    metadata=metadata_bag,
                )

            if load > self._wait_load_threshold:
                return GovernanceResult.wait(
                    reason=f"Cluster load {load:.1f}% exceeds wait threshold "
                           f"({self._wait_load_threshold}%)",
                    suggested_delay=60,
                    metadata=metadata_bag,
                )

        # 3. Check graph-level cluster requirements
        graph_meta = getattr(graph, "metadata", {}) or {}
        min_nodes = graph_meta.get("min_online_nodes")
        if min_nodes and self._get_online_node_count:
            online = metadata_bag.get("online_nodes", self._get_online_node_count())
            if online < min_nodes:
                return GovernanceResult.wait(
                    reason=f"Graph requires {min_nodes} nodes, only {online} online",
                    suggested_delay=30,
                    metadata=metadata_bag,
                )

        return GovernanceResult.allowed(
            reason="Cluster healthy",
            metadata=metadata_bag,
        )
