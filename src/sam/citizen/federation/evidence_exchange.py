# Distributed Evidence Exchange - WP-24
# IP-3.4-003 (AO-3.4-001, paket ketiga - Distributed Governance Intelligence)
#
# Pertukaran EVIDENCE GRAPH antar federation.
#
# Guardrail IP-3.4-003:
#   Evidence Exchange != Runtime Sharing (DGI-02)
#   Evidence-first (DGI-08)
#   Sovereignty preserved (DGI-06)
#
# Evidence = bukti DARI MANA kesimpulan lokal diturunkan (referensi,
# observasi, kontrak, keputusan). Dipertukarkan sebagai DUKUNGAN REASONING,
# bukan sebagai state runtime yang dibagi.
#
# Evidence graph = node (klaim/bukti) + edge (hubungan mendukung). Read-only.
# TIDAK ada sinkronisasi state, TIDAK ada eksekusi, TIDAK ada jaringan.

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class EvidenceNode:
    """Satu node dalam evidence graph (klaim atau bukti)."""

    node_id: str
    source_id: str
    kind: str            # claim | observation | contract | decision
    label: str
    detail: str = ""
    weight: float = 1.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "source_id": self.source_id,
            "kind": self.kind,
            "label": self.label,
            "detail": self.detail,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class EvidenceEdge:
    """Hubungan antar node dalam evidence graph (read-only)."""

    source_node: str
    target_node: str
    relation: str       # supports | refutes | derives-from

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_node": self.source_node,
            "target_node": self.target_node,
            "relation": self.relation,
        }


@dataclass(frozen=True)
class EvidenceGraph:
    """Kumpulan evidence nodes + edges dari satu sumber (read-only)."""

    source_id: str
    nodes: Tuple[EvidenceNode, ...] = ()
    edges: Tuple[EvidenceEdge, ...] = ()
    is_runtime_share: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "nodes": [n.as_dict() for n in self.nodes],
            "edges": [e.as_dict() for e in self.edges],
            "is_runtime_share": self.is_runtime_share,
        }


class DistributedEvidenceExchange:
    """Menyusun & membaca evidence graph antar federation (read-only).

    murni in-memory DTO - tidak ada transport jaringan, tidak ada
    sinkronisasi state. is_runtime_share selalu False: evidence exchange
    bukan runtime sharing.
    """

    def build_graph(
        self,
        source_id: str,
        nodes: Tuple[EvidenceNode, ...],
        edges: Tuple[EvidenceEdge, ...],
    ) -> EvidenceGraph:
        return EvidenceGraph(
            source_id=source_id,
            nodes=tuple(sorted(nodes, key=lambda n: n.node_id)),
            edges=tuple(sorted(edges, key=lambda e: (e.source_node,
                                                     e.target_node))),
            is_runtime_share=False,
        )

    def supports(
        self,
        graph: EvidenceGraph,
        claim_node_id: str,
    ) -> Tuple[EvidenceNode, ...]:
        """Bukti yang mendukung sebuah klaim (follow edges)."""
        support_ids = {
            e.source_node for e in graph.edges
            if e.target_node == claim_node_id and e.relation == "supports"
        }
        return tuple(
            n for n in graph.nodes
            if n.node_id in support_ids and n.kind != "claim")

    def exposes_runtime(self, graph: EvidenceGraph) -> bool:
        """Evidence exchange tidak pernah membagikan state runtime."""
        return graph.is_runtime_share
