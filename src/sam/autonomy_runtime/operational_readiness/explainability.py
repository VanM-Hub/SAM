# Readiness Explainability - WP-46
# IP-3.2-005 (AO-3.2-001 / ED-3.2-005)
#
# Menjelaskan MENGAPA penilaian kesiapan operasional mencapai kesimpulan
# tertentu. Menjembatani hasil agregasi & rekomendasi ke alasan yang bisa
# dipahami & diaudit. Prinsip: read-only, explainable, evidence-backed.
# Deterministic: input identik -> penjelasan identik.

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.operational_readiness.models import OperationalReadiness
from sam.autonomy_runtime.operational_readiness.coordination_intelligence import (
    CoordinationIntelligence,
)
from sam.autonomy_runtime.operational_readiness.risk import OperationalRiskReport


@dataclass(frozen=True)
class ReadinessExplanationItem:
    """Satu penjelasan aspek kesiapan (immutable)."""

    subject: str
    what: str
    why: str
    evidence: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "what": self.what,
            "why": self.why,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class ReadinessExplanation:
    """Penjelasan komprehensif kesimpulan kesiapan (immutable)."""

    explanation_id: str
    basis: str
    items: Tuple[ReadinessExplanationItem, ...] = ()
    conclusion: str = ""
    is_proposal_only: bool = True
    evidence: Tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "basis": self.basis,
            "items": [i.as_dict() for i in self.items],
            "conclusion": self.conclusion,
            "is_proposal_only": self.is_proposal_only,
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
        }

    def item_count(self) -> int:
        return len(self.items)


class ReadinessExplainer:
    """Menjelaskan keputusan kesiapan operasional (deterministik)."""

    def explain(
        self,
        readiness: OperationalReadiness,
        coordination: Optional[CoordinationIntelligence] = None,
        risk_report: Optional[OperationalRiskReport] = None,
        explanation_id: str = "",
    ) -> ReadinessExplanation:
        items: List[ReadinessExplanationItem] = []

        # 1) kesimpulan overall
        items.append(ReadinessExplanationItem(
            subject="overall",
            what="overall level {}".format(readiness.overall_level),
            why="aggregated {} inputs across {} dimensions".format(
                readiness.input_count(), readiness.dimension_count()),
            evidence=(readiness.readiness_id,),
        ))

        # 2) setiap dimensi
        for d in readiness.dimensions:
            items.append(ReadinessExplanationItem(
                subject="dimension.{}".format(d.name),
                what="score {:.2f}, ready={}".format(d.score, d.ready),
                why=d.detail,
                evidence=tuple(d.contributing_inputs),
            ))

        # 3) blocker
        for b in readiness.blockers:
            items.append(ReadinessExplanationItem(
                subject="blocker", what="blocking", why=b,
                evidence=tuple(readiness.evidence),
            ))

        # 4) koordinasi (konsistensi)
        if coordination:
            for c in coordination.consistency:
                items.append(ReadinessExplanationItem(
                    subject="consistency.{}".format(c.kind),
                    what=c.kind, why=c.detail,
                    evidence=tuple(c.involves),
                ))

        # 5) risiko terbesar
        top_risk = risk_report.highest_risk() if risk_report else None
        if top_risk:
            items.append(ReadinessExplanationItem(
                subject="risk.top",
                what="highest risk {:.2f}".format(top_risk.score),
                why=top_risk.name,
                evidence=(top_risk.basis,),
            ))

        all_evidence = tuple(
            dict.fromkeys(list(readiness.evidence) + [e for i in items for e in i.evidence])
        )
        return ReadinessExplanation(
            explanation_id=explanation_id or self._stable_id(readiness.readiness_id),
            basis="explanation derived from operational readiness integration",
            items=tuple(items),
            conclusion="operational readiness stated; no action selected",
            is_proposal_only=True,
            evidence=all_evidence,
            metadata={"deterministic": True},
        )

    @staticmethod
    def _stable_id(seed: str) -> str:
        return "oe-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
