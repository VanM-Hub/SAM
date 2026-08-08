# Federation Risk Assessment - WP-34
# IP-3.4-004 (AO-3.4-001, paket keempat - Federation Operational Coordination
# & Ecosystem Readiness)
#
# Identifikasi bottleneck operasional Federation dari readiness kolektif.
#
# Guardrail IP-3.4-004:
#   Readiness != Execution (OR-01)
#   Aggregation != Authority (OR-04)
#   Deterministic aggregation (OR-09)
#   Evidence-first readiness (OR-08)
#
# Risk assessment = penilaian risiko/kemacetan (bottleneck). BUKAN failover,
# BUKAN load balancing, BUKAN penjadwalan ulang. Hanya mengidentifikasi.

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from sam.citizen.federation.aggregation import (
    FederationReadinessAggregate,
)
from sam.citizen.federation.operational_readiness import (
    READINESS_DIMENSIONS,
)

# Ambang untuk menandai dimensi bottleneck (deterministik)
_BOTTLENECK_THRESHOLD = 0.4
_RISK_THRESHOLD = 0.4


@dataclass(frozen=True)
class FederationRisk:
    """Satu risiko operasional Federation (read-only, assessment)."""

    kind: str                # dimension-bottleneck / member-not-ready / no-members
    target: str
    severity: str            # low/medium/high
    description: str
    recommendation: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "target": self.target,
            "severity": self.severity,
            "description": self.description,
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True)
class FederationRiskAssessment:
    """Hasil penilaian risiko/kemacetan Federation (read-only)."""

    risks: Tuple[FederationRisk, ...] = ()
    overall: float = 0.0
    level: str = "low"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "risks": [r.as_dict() for r in self.risks],
            "overall": self.overall,
            "level": self.level,
        }


class FederationRiskAssessor:
    """Identifikasi bottleneck operasional Federation (read-only, deterministic)."""

    def assess(
        self,
        aggregate: FederationReadinessAggregate,
    ) -> FederationRiskAssessment:
        if not aggregate.members:
            return FederationRiskAssessment(
                risks=(FederationRisk(
                    kind="no-members",
                    target="federation",
                    severity="medium",
                    description="tidak ada anggota untuk menilai kesiapan",
                    recommendation="kumpulkan readiness anggota terlebih dulu",
                ),),
                overall=0.0,
                level="medium",
            )

        risks: list = []

        # 1) dimensi bottleneck (dibawah ambang)
        avgs = aggregate.dimension_averages
        for dim in READINESS_DIMENSIONS:
            avg = avgs.get(dim)
            if avg is None:
                continue
            if avg < _BOTTLENECK_THRESHOLD:
                severity = "high" if avg < 0.25 else "medium"
                risks.append(FederationRisk(
                    kind="dimension-bottleneck",
                    target=dim,
                    severity=severity,
                    description=("dimensi {d} rata-rata readiness "
                                 "{s:.0%} (di bawah ambang {t:.0%})".format(
                                     d=dim, s=avg, t=_BOTTLENECK_THRESHOLD)),
                    recommendation=("anggota dengan skor rendah pada {d} dapat "
                                    "meningkatkan kesiapan melalui evidence "
                                    "lokal; keputusan tetap lokal".format(d=dim)),
                ))

        # 2) anggota not-ready (bottleneck kandidat)
        for m in aggregate.members:
            if m.overall < _RISK_THRESHOLD:
                risks.append(FederationRisk(
                    kind="member-not-ready",
                    target=m.member_id,
                    severity="high" if m.overall < 0.2 else "medium",
                    description=("anggota {m} readiness {s:.0%} di bawah "
                                 "ambang".format(m=m.member_id,
                                                 s=m.overall)),
                    recommendation=("anggota {m} dapat meningkatkan kesiapan "
                                    "secara lokal; bukan kewenangan "
                                    "federation untuk mengubahnya".format(
                                        m=m.member_id)),
                ))

        # overall risk = 1 - readiness overall (skala risiko)
        overall_risk = round(max(0.0, 1.0 - aggregate.overall), 4)
        level = "high" if overall_risk >= 0.6 else (
            "medium" if overall_risk >= 0.3 else "low")

        return FederationRiskAssessment(
            risks=tuple(risks),
            overall=overall_risk,
            level=level,
        )
