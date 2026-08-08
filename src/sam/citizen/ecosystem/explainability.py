# Ecosystem Explainability - WP-26
# IP-3.3-003 (AO-3.3-001 / ED-3.3-001 cycle 3)
#
# Menjelaskan hasil sertifikasi & rekomendasi ekosistem secara evidence-backed.
# Setiap klaim (certification / health / recommendation / intelligence)
# dapat ditelusuri kembali ke evidence & basis penilaian.

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class EcosystemExplanation:
    """Eksplanasi sertifikasi & rekomendasi (immutable, evidence-backed)."""

    subject: str
    statements: Tuple[str, ...] = ()
    evidence_items: Tuple[str, ...] = ()
    basis: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, object]:
        return {
            "subject": self.subject,
            "statements": list(self.statements),
            "evidence_items": list(self.evidence_items),
            "basis": list(self.basis),
        }


class EcosystemExplainer:
    """Membangun eksplanasi deterministik atas hasil ekosistem."""

    def explain_certification(self, cert) -> EcosystemExplanation:
        c = getattr(cert, "as_dict", lambda: {})()
        statements = (
            "citizen {} maturity={} compliance={}".format(
                c.get("citizen_identity_id"),
                c.get("maturity"), c.get("compliance")),
            "qualified (estimator): {}".format(c.get("qualified")),
        )
        return EcosystemExplanation(
            subject="certification " + c.get("certification_id", ""),
            statements=statements,
            evidence_items=tuple(c.get("evidence", ())),
            basis=tuple(c.get("basis", ())),
        )

    def explain_health(self, health) -> EcosystemExplanation:
        h = getattr(health, "as_dict", lambda: {})()
        statements = (
            "overall ecosystem health: {}".format(h.get("overall")),
            "healthy {} / {} citizens".format(h.get("healthy_count"),
                                              h.get("citizen_count")),
        )
        return EcosystemExplanation(
            subject="ecosystem health",
            statements=statements,
            evidence_items=(
                "degraded: {}".format(h.get("degraded_count", 0)),
                "unavailable: {}".format(h.get("unavailable_count", 0)),
            ),
            basis=tuple(h.get("basis", ())),
        )

    def explain_recommendation(self, rec) -> EcosystemExplanation:
        r = getattr(rec, "as_dict", lambda: {})()
        return EcosystemExplanation(
            subject="recommendation " + r.get("recommendation_id", ""),
            statements=(
                "priority {}: {}".format(r.get("priority"), r.get("suggestion")),
                "advisory: {}".format(r.get("basis", [])),
            ),
            evidence_items=tuple(r.get("evidence", ())),
            basis=tuple(r.get("basis", ())),
        )
