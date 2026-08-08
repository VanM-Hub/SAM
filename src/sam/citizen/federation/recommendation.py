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
#
# ---------------------------------------------------------------------------
# + WP-35       Coordination Recommendation (IP-3.4-004)
# Guardrail IP-3.4-004:
#   Recommendation != Command (OR-03)
#   Evidence-first readiness (OR-08)
#   Local sovereignty preserved (OR-06)

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from sam.citizen.federation.intelligence import (
    FederationInsight,
    LocalReasoning,
)
from sam.citizen.federation.aggregation import (
    FederationReadinessAggregate,
)
from sam.citizen.federation.coordination_intelligence import (
    CoordinationInsight,
)
from sam.citizen.federation.risk import (
    FederationRiskAssessment,
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


# ---------------------------------------------------------------------------
# WP-35 - Coordination Recommendation (IP-3.4-004)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CoordinationRecommendation:
    """Rekomendasi koordinasi readiness (advisory, bukan perintah)."""

    focus: str
    suggestion: str
    priority: int = 0                 # 1=tertinggi (deterministik)
    basis: Tuple[str, ...] = ()
    is_command: bool = False          # OR-03 selalu False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "focus": self.focus,
            "suggestion": self.suggestion,
            "priority": self.priority,
            "basis": list(self.basis),
            "is_command": self.is_command,
        }


@dataclass(frozen=True)
class CoordinationRecommendationResult:
    """Hasil rekomendasi koordinasi (read-only, advisory)."""

    recommendations: Tuple[CoordinationRecommendation, ...] = ()
    federation_overall: float = 0.0
    is_command: bool = False          # OR-03 selalu False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "recommendations": [r.as_dict() for r in self.recommendations],
            "federation_overall": self.federation_overall,
            "is_command": self.is_command,
        }


class CoordinationRecommendationEngine:
    """Prioritaskan rekomendasi kolaborasi dari readiness & risk Federation.

    Rekomendasi disusun dari evidence readiness (OR-08) secara deterministik
    (OR-09). Tidak pernah menjadi perintah (OR-03: is_command selalu False).
    Federation hanya menyarankan; tidak memulai kolaborasi otomatis.
    """

    def recommend(
        self,
        aggregate: FederationReadinessAggregate,
        risk: FederationRiskAssessment,
        insights: Tuple[CoordinationInsight, ...],
    ) -> CoordinationRecommendationResult:
        recs: list = []
        priority = 1
        basis: list = []

        # 1) readiness overall belum siap -> fokus pada peningkatan kesiapan
        if aggregate.overall < 0.7:
            recs.append(CoordinationRecommendation(
                focus="federation-readiness",
                suggestion=("Kesiapan operasional Federation {s:.0%} belum "
                            "mencukupi untuk kolaborasi kolektif yang layak; "
                            "tingkatkan kesiapan anggota secara lokal."
                            .format(s=aggregate.overall)),
                priority=priority,
                basis=("overall:{:.2f}".format(aggregate.overall),),
                is_command=False,
            ))
            priority += 1

        # 2) bottleneck dimensi -> prioritas pada dimensi pembatas
        for r in risk.risks:
            if r.kind == "dimension-bottleneck":
                recs.append(CoordinationRecommendation(
                    focus="dimension-{}".format(r.target),
                    suggestion=("Dimensi {d} menjadi bottleneck operasional; "
                                "anggota dengan skor rendah dapat memperkuat "
                                "evidence lokal pada {d} (keputusan lokal)."
                                .format(d=r.target)),
                    priority=priority,
                    basis=("risk:{}".format(r.severity),),
                    is_command=False,
                ))
                priority += 1

        # 3) federasi siap & aligned -> rekomendasi kolaborasi yang layak
        if aggregate.overall >= 0.7:
            ready_members = [m.member_id for m in aggregate.members
                             if m.level == "ready"]
            recs.append(CoordinationRecommendation(
                focus="collaboration-eligible",
                suggestion=("Federation siap secara operasional ({n} anggota "
                            "ready); kolaborasi layak dipertimbangkan, namun "
                            "tetap memerlukan persetujuan masing-masing "
                            "anggota.".format(n=len(ready_members))),
                priority=priority,
                basis=("ready:{}:{}".format(len(ready_members),
                                             ",".join(ready_members)),),
                is_command=False,
            ))

        return CoordinationRecommendationResult(
            recommendations=tuple(recs),
            federation_overall=aggregate.overall,
            is_command=False,
        )
