# Coordination Intelligence - WP-33
# IP-3.4-004 (AO-3.4-001, paket keempat - Federation Operational Coordination
# & Ecosystem Readiness)
#
# Korelasi readiness lintas federation - memahami pola kesiapan kolektif
# (dimensi mana yang siap, mana yang menjadi pembatas, bagaimana distribusi
# readiness antar anggota).
#
# Guardrail IP-3.4-004:
#   Coordination != Orchestration (OR-02)
#   Federation Health != Runtime Control (OR-05)
#   Local sovereignty preserved (OR-06)
#   Deterministic aggregation (OR-09)
#
# Coordination intelligence = wawasan (insight) korelasi kesiapan antar
# federation. BUKAN menata/orchestrate eksekusi lintas federation.
# Federation memahami polanya; tidak pernah menjalankan kolaborasi otomatis.

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from sam.citizen.federation.aggregation import (
    FederationReadinessAggregate,
)
from sam.citizen.federation.operational_readiness import (
    READINESS_DIMENSIONS,
)


@dataclass(frozen=True)
class CoordinationInsight:
    """Wawasan koordinasi readiness lintas federation (read-only)."""

    focus: str
    pattern: str                     # aligned/imbalanced/gapped
    assessment: str
    detail: str
    weakest_dimension: Optional[str] = None
    strongest_dimension: Optional[str] = None
    weakest_member: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "focus": self.focus,
            "pattern": self.pattern,
            "assessment": self.assessment,
            "detail": self.detail,
            "weakest_dimension": self.weakest_dimension,
            "strongest_dimension": self.strongest_dimension,
            "weakest_member": self.weakest_member,
        }


class CoordinationIntelligence:
    """Analisis korelasi readiness lintas federation (read-only, deterministic)."""

    def analyze(
        self,
        aggregate: FederationReadinessAggregate,
    ) -> Tuple[CoordinationInsight, ...]:
        """Susun wawasan korelasi dari agregat readiness Federation."""
        if not aggregate.members:
            return (CoordinationInsight(
                focus="federation",
                pattern="gapped",
                assessment="no members",
                detail="tidak ada anggota untuk dinilai kesiapan",
            ),)

        insights: list = []

        # 1) pola keselarasan overall oleh distribusi level
        dist = aggregate.level_distribution
        ready = dist.get("ready", 0)
        total = len(aggregate.members)
        if ready == total:
            pattern = "aligned"
            assessment = ("seluruh anggota Federation siap secara operasional "
                          "untuk kolaborasi yang layak")
        elif ready == 0:
            pattern = "gapped"
            assessment = ("belum ada anggota Federation yang siap; kolaborasi "
                          "lintas-ekosistem belum layak")
        else:
            pattern = "imbalanced"
            assessment = ("kesiapan anggota Federation tidak merata; sebagian "
                          "siap, sebagian belum")
        insights.append(CoordinationInsight(
            focus="overall",
            pattern=pattern,
            assessment=assessment,
            detail=("ready={} partial={} not-ready={}".format(
                dist.get("ready", 0), dist.get("partial", 0),
                dist.get("not-ready", 0))),
        ))

        # 2) dimensi pembatas (weakest) & paling siap (strongest)
        avgs = aggregate.dimension_averages
        if avgs:
            weakest = min(avgs, key=lambda d: avgs[d])
            strongest = max(avgs, key=lambda d: avgs[d])
            insights.append(CoordinationInsight(
                focus="dimensions",
                pattern="gapped" if avgs[weakest] < 0.4 else "aligned",
                assessment=("dimensi {w} menjadi pembatas kesiapan kolektif "
                            "({ws:.0%}); dimensi {s} paling siap ({ss:.0%})."
                            .format(w=weakest, ws=avgs[weakest],
                                    s=strongest, ss=avgs[strongest])),
                detail="; ".join(
                    "{d}:{v:.2f}".format(d=d, v=avgs[d])
                    for d in READINESS_DIMENSIONS if d in avgs),
                weakest_dimension=weakest,
                strongest_dimension=strongest,
            ))

        # 3) anggota dengan readiness paling rendah (bottleneck kandidat)
        if aggregate.members:
            weakest_member = min(aggregate.members, key=lambda m: m.overall)
            insights.append(CoordinationInsight(
                focus="members",
                pattern="aligned"
                if weakest_member.level == "ready" else "imbalanced",
                assessment=("anggota {m} memiliki readiness terendah "
                            "({s:.0%}); ini menjadi perhatian kolektif "
                            "namun tetap keputusan lokal.".format(
                                m=weakest_member.member_id,
                                s=weakest_member.overall)),
                detail="",
                weakest_member=weakest_member.member_id,
            ))

        return tuple(insights)
