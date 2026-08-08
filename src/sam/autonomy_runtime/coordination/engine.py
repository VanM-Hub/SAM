# Runtime Coordination Engine - WP-32
# IP-3.2-004 (AO-3.2-001 / ED-3.2-004)
#
# Builds the coordination graph & coordination proposals from runtime topology.
# Prinsip: "Coordinate by model, never by orchestration."
# Coordination Engine hanya menghasilkan MODEL hubungan, urutan, dan proposal
# antarruntime. TIDAK boleh memicu aksi, dispatch, atau menjadi scheduler
# eksekusi. Proposal dihasilkan deterministik.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.coordination.models import (
    CoordinationMetadata,
    RuntimeNode,
    RuntimeTopology,
)


@dataclass(frozen=True)
class CoordinationEdge:
    """Satu hubungan koordinasi antarruntime (proposal/model, bukan aksi)."""

    src: str
    dst: str
    relation: str  # depends_on | peers_with | serves | governs
    rationale: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "src": self.src,
            "dst": self.dst,
            "relation": self.relation,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class CoordinationGraph:
    """Graph koordinasi runtime - kumpulan edge hubungan (model only)."""

    graph_id: str
    edges: Tuple[CoordinationEdge, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "edges": [e.as_dict() for e in self.edges],
            "metadata": dict(self.metadata),
        }

    def edge_count(self) -> int:
        return len(self.edges)

    def dependents_of(self, runtime_id: str) -> Tuple[str, ...]:
        """Runtime yang bergantung pada runtime_id (dst yang memerlukan src)."""
        return tuple(
            sorted({e.dst for e in self.edges if e.src == runtime_id})
        )

    def dependencies_of(self, runtime_id: str) -> Tuple[str, ...]:
        """Runtime yang menjadi prereq bagi runtime_id."""
        return tuple(
            sorted({e.src for e in self.edges if e.dst == runtime_id})
        )


@dataclass(frozen=True)
class CoordinationProposal:
    """Proposal koordinasi - urutan & hubungan yang DIUSULKAN (bukan aksi)."""

    proposal_id: str
    purpose: str
    steps: Tuple[Tuple[str, str], ...] = ()  # (runtime_id, action_proposal)
    graph: CoordinationGraph = field(default_factory=lambda: CoordinationGraph(graph_id=""))
    rationale: str = ""
    is_proposal_only: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "purpose": self.purpose,
            "steps": [list(s) for s in self.steps],
            "graph": self.graph.as_dict(),
            "rationale": self.rationale,
            "is_proposal_only": self.is_proposal_only,
            "metadata": dict(self.metadata),
        }

    def step_count(self) -> int:
        return len(self.steps)


class RuntimeCoordinationEngine:
    """Engine koordinasi: bangun graph + proposal koordinasi (deterministik)."""

    # label aksi proposal - harus selalu ber-prefix coordinate_ (proposal)
    _PROPOSAL_ACTIONS = (
        "coordinate_align", "coordinate_handshake", "coordinate_sync",
        "coordinate_rebalance",
    )

    def build_graph(
        self,
        topology: RuntimeTopology,
        graph_id: str = "",
    ) -> CoordinationGraph:
        edges: List[CoordinationEdge] = []
        for (src, dst) in topology.edges:
            edges.append(
                CoordinationEdge(
                    src=src,
                    dst=dst,
                    relation="depends_on",
                    rationale="prerequisite relationship observed in topology",
                )
            )
        graph_id = graph_id or self._stable_id(topology.topology_id)
        return CoordinationGraph(graph_id=graph_id, edges=tuple(sorted(
            edges, key=lambda e: (e.src, e.dst)
        )))

    def build_proposal(
        self,
        topology: RuntimeTopology,
        purpose: str,
        proposal_id: str = "",
    ) -> CoordinationProposal:
        """Bangun proposal koordinasi dari topology (deterministik, proposal-only)."""
        graph = self.build_graph(topology)
        ordered = self._order_runtimes(topology)
        steps: List[Tuple[str, str]] = []
        for rid in ordered:
            steps.append((rid, self._proposal_action_for(rid, topology)))
        proposal_id = proposal_id or self._stable_id(topology.topology_id)
        return CoordinationProposal(
            proposal_id=proposal_id,
            purpose=purpose,
            steps=tuple(steps),
            graph=graph,
            rationale=(
                "Coordination proposal derived from runtime topology; "
                "proposal only, no dispatch or orchestration"
            ),
            is_proposal_only=True,
            metadata={"deterministic": True},
        )

    def metadata(
        self,
        topology: RuntimeTopology,
        basis: str,
        coordination_id: str = "",
        created_at: str = "",
    ) -> CoordinationMetadata:
        return CoordinationMetadata(
            coordination_id=coordination_id or self._stable_id(topology.topology_id),
            created_at=created_at,
            basis=basis,
            phase="coordinative",
        )

    # --- helpers ---

    def _order_runtimes(self, topology: RuntimeTopology) -> Tuple[str, ...]:
        """Urutan deterministik: koordinator dahulu, lalu workers (sorted)."""
        nodes = sorted(topology.nodes, key=lambda n: (n.role, n.runtime_id))
        return tuple(n.runtime_id for n in nodes)

    @staticmethod
    def _proposal_action_for(runtime_id: str, topology: RuntimeTopology) -> str:
        return "coordinate_align"

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "co-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
