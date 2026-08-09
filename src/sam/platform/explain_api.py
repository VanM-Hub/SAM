# Explainability API - IP-3.5-004 (AO-ENG-001, MISSION-3.5)
# WP-28: facade read/assemble-only untuk Explainability Experience.
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail (IP-3.5): Explainability API bersifat READ/AGGREGATE/PRESENT only.
#   TIDAK ada: evidence verification, evidence rejection, decision output,
#   authority inference. Explainability PRESENTS evidence graph; never
#   judges evidence.

"""Explainability API (Facade).

Facade read-only untuk Explainability Experience. Menerima evidence dari
luar, membangun unified evidence graph, menghitung agregasi & penjelasan
lintas domain, serta melacak chain dukungan - murni presentasi.
"""

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from sam.platform.evidence_graph import (
    EvidenceAggregate,
    EvidenceGraph,
    EvidenceInput,
    aggregate_evidence,
    build_evidence_graph,
)
from sam.platform.explainability import (
    ExplainabilitySummary,
    explain_graph,
)
from sam.platform.evidence_chain import (
    EvidenceChain,
    build_chain,
    orphaned_evidence,
)


@dataclass(frozen=True)
class ExplainabilitySnapshot:
    """Snapshot baca-saja Explainability Experience.

    Menyajikan graph + agregasi + penjelasan; tidak memegang otoritas
    verifikasi evidence.
    """

    graph: EvidenceGraph
    aggregate: EvidenceAggregate
    summary: ExplainabilitySummary


class ExplainabilityAPI:
    """Facade read-only untuk Explainability Experience.

    Menerima evidence dari luar, menyusun graph & penjelasan, dan
    menyajikannya. DILARANG memverifikasi/menolak evidence atau memutuskan
    otoritas.
    """

    def __init__(self) -> None:
        self._evidence: dict = {}

    def register_evidence(self, evidence: EvidenceInput) -> None:
        self._evidence[evidence.evidence_id] = evidence

    def graph(self) -> EvidenceGraph:
        return build_evidence_graph(self._evidence.values())

    def aggregate(self) -> EvidenceAggregate:
        return aggregate_evidence(self.graph())

    def summary(self) -> ExplainabilitySummary:
        return explain_graph(self.graph())

    def snapshot(self) -> ExplainabilitySnapshot:
        g = self.graph()
        return ExplainabilitySnapshot(
            graph=g,
            aggregate=aggregate_evidence(g),
            summary=explain_graph(g),
        )

    def chain(self, evidence_id: str) -> Optional[EvidenceChain]:
        return build_chain(self.graph(), evidence_id)

    def orphans(self):
        return orphaned_evidence(self.graph())

    def evidence_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._evidence.keys()))
