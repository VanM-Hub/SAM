# Coordination API - WP-37
# IP-3.2-004 (AO-3.2-001 / ED-3.2-004)
#
# Fasad read-only untuk koordinasi & lifecycle runtime.
# Prinsip: "Coordinate by model, never by orchestration."
# API ini hanya menyajikan MODEL koordinasi & PROPOSAL lifecycle - tidak pernah
# melakukan dispatch, orchestration, start/stop/restart, atau mutasi any state.

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from sam.autonomy_runtime.coordination.engine import (
    CoordinationGraph,
    CoordinationProposal,
    RuntimeCoordinationEngine,
)
from sam.autonomy_runtime.coordination.dependency import (
    DependencyCoordinationPlan,
    DependencyCoordinator,
)
from sam.autonomy_runtime.coordination.models import RuntimeTopology
from sam.autonomy_runtime.lifecycle.analyzer import LifecycleAnalyzer
from sam.autonomy_runtime.lifecycle.models import LifecycleState
from sam.autonomy_runtime.lifecycle.planner import (
    LifecyclePlan,
    LifecyclePlanner,
)


@dataclass(frozen=True)
class CoordinationSummary:
    """Rangkuman koordinasi runtime (immutable)."""

    topology_id: str
    runtime_count: int
    edge_count: int
    coordination_proposal_count: int
    dependency_blocker_count: int
    lifecycle_plan_count: int
    basis: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "topology_id": self.topology_id,
            "runtime_count": self.runtime_count,
            "edge_count": self.edge_count,
            "coordination_proposal_count": self.coordination_proposal_count,
            "dependency_blocker_count": self.dependency_blocker_count,
            "lifecycle_plan_count": self.lifecycle_plan_count,
            "basis": self.basis,
            "metadata": dict(self.metadata),
        }


class CoordinationAPI:
    """Fasad read-only koordinasi & lifecycle runtime."""

    def __init__(
        self,
        coord_engine: Optional[RuntimeCoordinationEngine] = None,
        dep_coordinator: Optional[DependencyCoordinator] = None,
        life_analyzer: Optional[LifecycleAnalyzer] = None,
        life_planner: Optional[LifecyclePlanner] = None,
    ):
        self._coord = coord_engine or RuntimeCoordinationEngine()
        self._dep = dep_coordinator or DependencyCoordinator()
        self._life_analyzer = life_analyzer or LifecycleAnalyzer()
        self._life_planner = life_planner or LifecyclePlanner(self._life_analyzer)

    def topologize(
        self,
        nodes: Tuple[Any, ...],
        edges: Tuple[Tuple[str, str], ...],
        topology_id: str = "",
        created_at: str = "",
        basis: str = "runtime registry observation",
    ) -> RuntimeTopology:
        """Bangun RuntimeTopology dari node & edge (read-only, model only)."""
        return RuntimeTopology(
            topology_id=topology_id or self._stable_id(
                "-".join(sorted(e[0] for e in edges)) or "topo"
            ),
            created_at=created_at,
            nodes=tuple(nodes),
            edges=tuple(edges),
            basis=basis,
        )

    def coordinate(
        self,
        topology: RuntimeTopology,
        purpose: str = "align runtime topology",
    ) -> CoordinationProposal:
        """Bangun proposal koordinasi (model, bukan orchestration)."""
        return self._coord.build_proposal(topology, purpose)

    def dependency_plan(
        self,
        topology: RuntimeTopology,
    ) -> DependencyCoordinationPlan:
        """Bangun rencana koordinasi berdasar dependency (proposal)."""
        graph = self._coord.build_graph(topology)
        return self._dep.build_plan(topology, graph)

    def lifecycle_plan(
        self,
        states: Tuple[LifecycleState, ...],
        target_runtime_id: str = "",
    ) -> LifecyclePlan:
        """Susun rencana lifecycle (proposal transisi + readiness)."""
        return self._life_planner.plan(states, target_runtime_id)

    def lifecycle_analyze(
        self,
        state: LifecycleState,
    ):
        return self._life_analyzer.analyze(state)

    def summarize(
        self,
        topology: RuntimeTopology,
        lifecycles: Tuple[LifecycleState, ...] = (),
    ) -> CoordinationSummary:
        """Rangkuman kondisi koordinasi & lifecycle (read-only)."""
        proposal = self.coordinate(topology)
        dep = self.dependency_plan(topology)
        plans = 0
        if lifecycles:
            try:
                self.lifecycle_plan(lifecycles)
                plans = 1
            except Exception:
                plans = 0
        return CoordinationSummary(
            topology_id=topology.topology_id,
            runtime_count=topology.node_count(),
            edge_count=topology.edge_count(),
            coordination_proposal_count=proposal.step_count(),
            dependency_blocker_count=dep.blocker_count(),
            lifecycle_plan_count=plans,
            basis=topology.basis,
            metadata={"deterministic": True},
        )

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "topo-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
