# Readiness Aggregation Engine - WP-32
# IP-3.4-004 (AO-3.4-001, paket keempat - Federation Operational Coordination
# & Ecosystem Readiness)
#
# Agregasi readiness seluruh anggota Federation menjadi satu gambaran
# kesiapan operasional Federation.
#
# Guardrail IP-3.4-004:
#   Aggregation != Authority (OR-04)
#   Deterministic aggregation (OR-09)
#   Evidence-first readiness (OR-08)
#
# Agregasi = perhitungan statistik deterministik (rata-rata tertimbang,
# distribusi level). Menghasilkan penilaian kolektif; BUKAN otoritas.
# Federation "memahami" kesiapan kolektif, tidak pernah bertindak atasnya.

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from sam.citizen.federation.operational_readiness import (
    FederationReadiness,
    READINESS_DIMENSIONS,
    categorize_overall,
)

# Level readiness untuk distribusi
_LEVELS = ("ready", "partial", "not-ready")


@dataclass(frozen=True)
class FederationReadinessAggregate:
    """Gambaran kesiapan operasional kolektif Federation (read-only)."""

    members: Tuple[FederationReadiness, ...] = ()
    overall: float = 0.0
    level: str = "unknown"
    dimension_averages: Dict[str, float] = None
    level_distribution: Dict[str, int] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimension_averages",
                           self.dimension_averages or {})
        object.__setattr__(self, "level_distribution",
                           self.level_distribution or {})

    def as_dict(self) -> Dict[str, Any]:
        return {
            "members": [m.as_dict() for m in self.members],
            "overall": self.overall,
            "level": self.level,
            "dimension_averages": dict(self.dimension_averages),
            "level_distribution": dict(self.level_distribution),
            "member_count": len(self.members),
        }


class FederationReadinessAggregator:
    """Agregasi readiness seluruh anggota Federation (read-only, deterministic).

    Tidak ada otoritas terbentuk: agregasi hanyalah ringkasan statistik
    readiness anggota yang berdaulat. Setiap anggota tetap memutuskan sendiri.
    """

    def aggregate(
        self,
        members: Tuple[FederationReadiness, ...],
    ) -> FederationReadinessAggregate:
        if not members:
            return FederationReadinessAggregate(
                members=members,
                overall=0.0,
                level="not-ready",
            )

        # rata-rata member (bobot sama per anggota - setiap federation berdaulat)
        overall = (
            sum(m.overall for m in members) / float(len(members))
        )

        # rata-rata per dimensi (hanya anggota yang punya skor dimensi)
        dim_sums: Dict[str, float] = {}
        dim_counts: Dict[str, int] = {}
        for m in members:
            for dim in READINESS_DIMENSIONS:
                s = m.score(dim)
                if s is not None:
                    dim_sums[dim] = dim_sums.get(dim, 0.0) + s
                    dim_counts[dim] = dim_counts.get(dim, 0) + 1
        dim_avgs = {
            d: (dim_sums[d] / dim_counts[d]) if dim_counts.get(d) else 0.0
            for d in READINESS_DIMENSIONS
        }

        # distribusi level anggota
        dist = {lvl: sum(1 for m in members if m.level == lvl)
                for lvl in _LEVELS}

        return FederationReadinessAggregate(
            members=members,
            overall=round(overall, 4),
            level=categorize_overall(overall),
            dimension_averages=dict(dim_avgs),
            level_distribution=dist,
        )
