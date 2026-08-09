# Cross-domain Explainability - IP-3.5-004 (AO-ENG-001, MISSION-3.5)
# WP-26 (Cross-domain Explainability).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail: Explainability != Decision Authority. Platform menjelaskan
#   hubungan evidence lintas domain; ia tidak mengambil keputusan apapun,
#   tidak menyimpulkan otoritas.

"""Cross-domain Explainability.

Menyediakan penjelasan observasional atas hubungan evidence lintas domain.
Platform menghitung coverage & keterjangkauan graph; tidak mengambil
keputusan / otoritas.
"""

from dataclasses import dataclass
from typing import Optional, Sequence, Set, Tuple

from sam.platform.evidence_graph import EvidenceGraph, EvidenceNode, EvidenceLink


@dataclass(frozen=True)
class DomainPairCoverage:
    """Cakupan hubungan antara dua domain (observasional)."""

    source_domain: str
    target_domain: str
    link_count: int = 0

    @property
    def has_cross_domain_evidence(self) -> bool:
        return self.source_domain != self.target_domain and self.link_count > 0


@dataclass(frozen=True)
class ExplainabilitySummary:
    """Ringkasan penjelasan graph (deterministik, read-only)."""

    total_nodes: int = 0
    total_links: int = 0
    domains: Tuple[str, ...] = ()
    cross_domain_links: int = 0
    coverage_pairs: Tuple[DomainPairCoverage, ...] = ()

    @property
    def explainable(self) -> bool:
        # Graph dengan node + link antar-domain dapat dijelaskan lintas domain.
        return self.total_nodes > 0 and self.cross_domain_links > 0


def _link_domains(graph: EvidenceGraph) -> Tuple[Tuple[str, str], ...]:
    """Domain pasangan untuk tiap link (deterministik)."""
    pairs = []
    for link in graph.links:
        src = graph.node(link.source)
        tgt = graph.node(link.target)
        if src is None or tgt is None:
            continue
        pairs.append((src.domain, tgt.domain))
    return tuple(pairs)


def explain_graph(graph: EvidenceGraph) -> ExplainabilitySummary:
    """Penjelasan observasional graph evidence (deterministik)."""
    pairs = _link_domains(graph)
    cross = sum(1 for s, t in pairs if s != t)
    # coverage per pasangan domain (urut deterministik)
    pair_counts: dict = {}
    for (s, t) in pairs:
        key = (s, t)
        pair_counts[key] = pair_counts.get(key, 0) + 1
    coverage = tuple(
        DomainPairCoverage(s, t, c)
        for (s, t), c in sorted(pair_counts.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    )
    return ExplainabilitySummary(
        total_nodes=graph.node_count,
        total_links=graph.link_count,
        domains=graph.domain_set(),
        cross_domain_links=cross,
        coverage_pairs=coverage,
    )
