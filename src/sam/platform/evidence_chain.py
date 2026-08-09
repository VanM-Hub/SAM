# Evidence Chain Viewer - IP-3.5-004 (AO-ENG-001, MISSION-3.5)
# WP-27 (Evidence Chain Viewer).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail: Chain Viewer != Verification Authority. Platform melacak rantai
#   dukungan evidence (siapa mendukung siapa); ia tidak memverifikasi/
#   menolak evidence.

"""Evidence Chain Viewer.

Menyediakan pelacakan rantai dukungan evidence (chain) untuk menampilkan
bagaimana satu evidence didukung oleh evidence lain. Murni navigasi graph;
bukan penilaian validitas.
"""

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from sam.platform.evidence_graph import EvidenceGraph, EvidenceNode


@dataclass(frozen=True)
class EvidenceChain:
    """Rantai dukungan menuju satu evidence (presentation).

    Merepresentasikan urutan node pendukung (dari akar ke target) tanpa
    menilai validitas isi evidence.
    """

    target_id: str
    # Node pendukung berurutan (akar -> target).
    path: Tuple[EvidenceNode, ...] = ()

    @property
    def depth(self) -> int:
        return len(self.path)


def _chain_path(graph: EvidenceGraph, target: str, max_depth: int = 8) -> Tuple[str, ...]:
    """Cari rantai pendukung ke target (deterministik, BFS mundur).

    pred[x] = dukungan source yang langsung mendukung x. Hasil: urut akar ->
    target (node yang paling dasar mendukung muncul pertama).
    """
    pred: dict = {}
    for link in graph.links:
        pred.setdefault(link.target, []).append(link.source)
    for k in pred:
        pred[k].sort()
    result = [target]
    visited = {target}
    queue = [target]
    while queue:
        cur = queue.pop(0)
        for src in pred.get(cur, ()):
            if src not in visited:
                visited.add(src)
                result.insert(0, src)
                queue.append(src)
        if len(result) > max_depth:
            break
    return tuple(result)


def build_chain(graph: EvidenceGraph, target: str) -> Optional[EvidenceChain]:
    """Bangun rantai dukungan untuk evidence target.

    Mengembalikan None bila target tidak ada di graph.
    """
    node = graph.node(target)
    if node is None:
        return None
    path_ids = _chain_path(graph, target)
    path_nodes = tuple(
        n for n in graph.nodes if n.evidence_id in set(path_ids)
    )
    # urutkan sesuai urutan path_ids
    order = {eid: i for i, eid in enumerate(path_ids)}
    path_nodes = tuple(sorted(path_nodes, key=lambda n: order[n.evidence_id]))
    return EvidenceChain(target_id=target, path=path_nodes)


def orphaned_evidence(graph: EvidenceGraph) -> Tuple[EvidenceNode, ...]:
    """Evidence tanpa link sama sekali (akar/orphan) - deterministik."""
    linked = {l.source for l in graph.links} | {l.target for l in graph.links}
    return tuple(n for n in graph.nodes if n.evidence_id not in linked)
