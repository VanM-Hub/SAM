# Ecosystem Recommendation - WP-25
# IP-3.3-003 (AO-3.3-001 / ED-3.3-001 cycle 3)
#
# Rekomendasi berbasis evidence untuk peningkatan ekosistem. Seluruh
# rekomendasi bersifat ADVISORY (Recommendation != Authority) - tidak ada
# yang diterapkan otomatis. Output deterministik & evidence-backed.

from dataclasses import dataclass
from typing import Dict, Sequence, Tuple


@dataclass(frozen=True)
class EcosystemRecommendation:
    """Rekomendasi peningkatan ekosistem (immutable, advisory)."""

    recommendation_id: str
    subject: str
    suggestion: str
    priority: str          # "low" | "medium" | "high"
    evidence: Tuple[str, ...] = ()
    basis: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, object]:
        return {
            "recommendation_id": self.recommendation_id,
            "subject": self.subject,
            "suggestion": self.suggestion,
            "priority": self.priority,
            "evidence": list(self.evidence),
            "basis": list(self.basis),
        }

    @property
    def advisory(self) -> bool:
        # SEMUA rekomendasi advisory (tidak pernah diterapkan otomatis)
        return True


class EcosystemRecommendationEngine:
    """Menghasilkan rekomendasi peningkatan (advisory, evidence-first)."""

    _seq = 0

    def recommend(self, health: "object",
                  snapshot: "object",
                  certifications: Dict[str, object] = None
                  ) -> Tuple[EcosystemRecommendation, ...]:
        """Rekomendasikan peningkatan berdasarkan bukti agregat.

        Deterministik: urutan rekomendasi stabil (mengurutkan suggestion).
        """
        recs: list = []
        certs = certifications or {}

        # 1. health degraded -> rekomendasi perhatian availability
        h = getattr(health, "as_dict", lambda: {})()
        if h.get("overall") == "degraded" and h.get("unavailable_count", 0) > 0:
            recs.append(EcosystemRecommendation(
                recommendation_id=self._next_id("eco"),
                subject="ecosystem availability",
                suggestion="address unavailable citizens to restore ecosystem health",
                priority="high",
                evidence=(
                    "unavailable: {}".format(h.get("unavailable_count", 0)),
                    "overall: {}".format(h.get("overall")),
                ),
                basis=("recommendation != authority", "evidence-first"),
            ))

        # 2. certification noncompliance -> rekomendasi peningkatan compliance
        for cid, cert in certs.items():
            cdict = getattr(cert, "as_dict", lambda: {})()
            if cdict.get("compliance") in ("noncompliant", "partial"):
                recs.append(EcosystemRecommendation(
                    recommendation_id=self._next_id("eco"),
                    subject="citizen compliance: " + cid,
                    suggestion="improve certification compliance to reach compliant",
                    priority="medium" if cdict.get("compliance") == "partial" else "high",
                    evidence=(
                        "compliance: {}".format(cdict.get("compliance")),
                        "checks {}/{}".format(cdict.get("checks_passed"),
                                              cdict.get("checks_total")),
                    ),
                    basis=("recommendation != authority", "evidence-first"),
                ))

        # sort deterministik (by subject) lalu fix id gabungan
        recs = sorted(recs, key=lambda r: r.subject)
        out = []
        for idx, r in enumerate(recs):
            out.append(EcosystemRecommendation(
                recommendation_id="eco-{:04d}".format(idx + 1),
                subject=r.subject,
                suggestion=r.suggestion,
                priority=r.priority,
                evidence=r.evidence,
                basis=r.basis,
            ))
        return tuple(out)

    @staticmethod
    def _next_id(prefix: str) -> str:
        # placeholder - id final ditetapkan saat urutan disortir
        return "{}--tmp".format(prefix)
