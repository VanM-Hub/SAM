# Distributed Recommendation - WP-26
# IP-3.4-003 (AO-3.4-001, paket ketiga - Distributed Governance Intelligence)
#
# Rekomendasi FEDERASI - saran yang disusun lintas federation.
#
# Guardrail IP-3.4-003:
#   Recommendation != Decision (DGI-03)
#   Evidence-first (DGI-08)
#   Sovereignty preserved (DGI-06)
#
# Rekomendasi = saran (advisory). BUKAN keputusan, BUKAN perintah.
# Rekomendasi disusun dari evidence/insight yang tersedia, secara
# deterministik; penerima bebas menerima/menolak.

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from sam.citizen.federation.intelligence import (
    FederationInsight,
    LocalReasoning,
)


@dataclass(frozen=True)
class FederationRecommendation:
    """Satu rekomendasi lintas federation (read-only, advisory)."""

    focus: str
    suggestion: str
    basis: Tuple[str, ...] = ()
    is_decision: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "focus": self.focus,
            "suggestion": self.suggestion,
            "basis": list(self.basis),
            "is_decision": self.is_decision,
        }


@dataclass(frozen=True)
class RecommendationResult:
    """Himpunan rekomendasi dari insight (tidak pernah memaksa)."""

    insights: Tuple[FederationInsight, ...]
    recommendations: Tuple[FederationRecommendation, ...] = ()
    is_decision: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "insights": [i.as_dict() for i in self.insights],
            "recommendations": [r.as_dict() for r in self.recommendations],
            "is_decision": self.is_decision,
        }


class DistributedRecommendation:
    """Menyusun rekomendasi dari insight federasi (read-only, deterministic).

    Rekomendasi dihasilkan dari skor kesepakatan & sinyal insight. Tidak
    pernah menghasilkan keputusan (is_decision selalu False). Advisory saja.
    """

    def recommend(
        self,
        insights: Tuple[FederationInsight, ...],
    ) -> RecommendationResult:
        recommendations: list = []
        for insight in insights:
            suggestion = None
            if insight.signal == "clear":
                suggestion = ("Anggota sepakat pada fokus {focus} "
                              "(agreement {score:.0%}); pertimbangkan untuk "
                              "menelusuri keinsightan bersama.".format(
                                  focus=insight.focus, score=insight.agreement_score))
            elif insight.signal == "mixed":
                suggestion = ("Anggota terbagi pada fokus {focus}; bandingkan "
                              "reasoning lokal sebelum menilai.".format(
                                  focus=insight.focus))
            else:
                suggestion = ("Bukti terbatas pada fokus {focus}; kumpulkan "
                              "lebih banyak evidence lokal.".format(
                                  focus=insight.focus))
            recommendations.append(FederationRecommendation(
                focus=insight.focus,
                suggestion=suggestion,
                basis=("agreement:{:.2f}".format(insight.agreement_score),),
                is_decision=False,
            ))
        return RecommendationResult(
            insights=insights,
            recommendations=tuple(recommendations),
            is_decision=False,
        )

    def for_member(
        self,
        member_id: str,
        insights: Tuple[FederationInsight, ...],
    ) -> Tuple[FederationRecommendation, ...]:
        """Rekomendasi yang relevan untuk satu anggota (berdasarkan reasoning-nya)."""
        result: list = []
        for insight in insights:
            member_reasoning = next(
                (r for r in insight.members if r.member_id == member_id),
                None)
            if member_reasoning is None:
                continue
            if insight.signal == "clear":
                suggestion = ("Sejalan dengan mayoritas pada fokus {focus}.".format(
                    focus=insight.focus))
            else:
                suggestion = ("Baru-baru ini menilai {focus} dengan "
                              "confidence {conf:.0%}; dukung dengan evidence "
                              "lokal.".format(focus=insight.focus,
                                              conf=member_reasoning.confidence))
            result.append(FederationRecommendation(
                focus=insight.focus,
                suggestion=suggestion,
                basis=("member:{}".format(member_id),),
                is_decision=False,
            ))
        return tuple(result)
