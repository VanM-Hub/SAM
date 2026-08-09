# Unified Evidence Graph - IP-3.5-004 (AO-ENG-001, MISSION-3.5)
# WP-24 (Unified Evidence Graph) + WP-25 (Evidence Aggregation).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# CAPABILITY BOUNDARY: platform MENERIMA evidence dari luar sebagai input.
#   Platform TIDAK mengimpor evidence internal secara deep; TIDAK
#   memverifikasi/menolak/menandai evidence (itu otoritas evidence runtime).
#   Platform mengagregasi & menyajikan graph evidence lintas domain.

"""Unified Evidence Graph & Aggregation.

Menyajikan grafik evidence yang menyatukan bukti dari berbagai domain
(mission, governance, runtime, citizen, federation) menjadi satu pandangan
yang koheren. Seluruh evidence DIBERIKAN sebagai input dataclass immutable;
platform hanya menghubungkan & menyajikan secara deterministik.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple


# --- Evidence input model (diberikan dari luar) -----------------------------

@dataclass(frozen=True)
class EvidenceInput:
    """Satu evidence yang DIBERIKAN ke platform untuk penyajian.

    Mencerminkan atribut evidence (id, domain, type, status, ref). Platform
    tidak memverifikasi evidence; ia hanya menyajikan.
    """

    evidence_id: str
    domain: str = ""          # mission | governance | runtime | citizen | federation ...
    type: str = ""            # label dari EvidenceType (mis. "DECISION_OUTCOME")
    status: str = ""          # dari EvidenceStatus (mis. "VERIFIED")
    summary: str = ""
    # Reference/evidence yang mendukung ini (chain parent ids).
    supports: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.evidence_id.strip():
            raise ValueError("evidence_id wajib diisi.")


def _norm_status(status: str) -> str:
    """Normalisasi status ke nilai enum EvidenceStatus terdekat.

    Bukan judgment; hanya kategorisasi label untuk tampilan.
    """
    s = (status or "").strip().upper()
    known = ("COLLECTED", "VERIFIED", "REJECTED", "EXPIRED", "ARCHIVED")
    if s in known:
        return s
    return "COLLECTED" if s else "COLLECTED"


@dataclass(frozen=True)
class EvidenceNode:
    """Node dalam grafik evidence (presentation view)."""

    evidence_id: str
    domain: str = ""
    status: str = "COLLECTED"
    summary: str = ""

    @property
    def status_norm(self) -> str:
        return _norm_status(self.status)


@dataclass(frozen=True)
class EvidenceLink:
    """Sambungan antar-node evidence (dukungan/chain)."""

    source: str
    target: str


@dataclass(frozen=True)
class EvidenceGraph:
    """Grafik evidence lintas domain (deterministik, immutable).

    Nodes + links yang dihitung dari input; murni representasi hubungan.
    """

    nodes: Tuple[EvidenceNode, ...] = ()
    links: Tuple[EvidenceLink, ...] = ()

    def domain_set(self) -> Tuple[str, ...]:
        return tuple(sorted({n.domain for n in self.nodes if n.domain}))

    def nodes_in_domain(self, domain: str) -> Tuple[EvidenceNode, ...]:
        return tuple(n for n in self.nodes if n.domain == domain)

    def node(self, evidence_id: str) -> Optional[EvidenceNode]:
        for n in self.nodes:
            if n.evidence_id == evidence_id:
                return n
        return None

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def link_count(self) -> int:
        return len(self.links)


# --- Aggregation (WP-25) -----------------------------------------------------

@dataclass(frozen=True)
class EvidenceAggregate:
    """Agregasi evidence lintas domain (deterministik).

    Per-domain count + status breakdown. Murni statistik observasional.
    """

    by_domain: Tuple[Tuple[str, int], ...] = ()
    total: int = 0
    verified_count: int = 0

    def count_for(self, domain: str) -> int:
        for d, c in self.by_domain:
            if d == domain:
                return c
        return 0


def build_evidence_graph(
    evidence: Sequence[EvidenceInput],
) -> EvidenceGraph:
    """Bangun grafik evidence dari input (deterministik)."""
    nodes = tuple(sorted(
        (EvidenceNode(e.evidence_id, e.domain, e.status, e.summary)
         for e in evidence),
        key=lambda n: n.evidence_id,
    ))
    links = []
    seen = set()
    for e in sorted(evidence, key=lambda x: x.evidence_id):
        for target in e.supports:
            key = (e.evidence_id, target)
            # jaga determinisme & hindari duplikat
            if key not in seen and _valid_target(target, evidence):
                seen.add(key)
                links.append(EvidenceLink(source=e.evidence_id, target=target))
    return EvidenceGraph(nodes=nodes, links=tuple(sorted(
        links, key=lambda l: (l.source, l.target))))


def _valid_target(target: str, evidence: Sequence[EvidenceInput]) -> bool:
    return any(e.evidence_id == target for e in evidence)


def aggregate_evidence(
    graph: EvidenceGraph,
) -> EvidenceAggregate:
    """Agregasi evidence per-domain (deterministik)."""
    counts: Dict[str, int] = {}
    verified = 0
    for n in graph.nodes:
        d = n.domain or "unknown"
        counts[d] = counts.get(d, 0) + 1
        if n.status_norm == "VERIFIED":
            verified += 1
    by_domain = tuple(sorted(counts.items()))
    return EvidenceAggregate(
        by_domain=by_domain,
        total=graph.node_count,
        verified_count=verified,
    )
