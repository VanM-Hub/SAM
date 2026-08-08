# Ecosystem Health Assessment - WP-24
# IP-3.3-003 (AO-3.3-001 / ED-3.3-001 cycle 3)
#
# Penilaian kesehatan KOLEKTIF Citizen ekosistem. Menggabungkan status health
# tiap Citizen menjadi gambaran agregat. Murni penilaian; TIDAK mengendalikan
# Citizen (Ecosystem Health != Runtime Control).

from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

# urutan tingkat kesehatan (rendah -> tinggi) utk agregasi deterministik
_HEALTH_ORDER = ("unknown", "unavailable", "degraded", "healthy")


def _health_level(status: str) -> str:
    s = status.strip().lower()
    return s if s in _HEALTH_ORDER else "unknown"


@dataclass(frozen=True)
class EcosystemHealthAssessment:
    """Penilaian kesehatan kolektif ekosistem (immutable)."""

    overall: str
    citizen_count: int
    healthy_count: int
    degraded_count: int
    unavailable_count: int
    unknown_count: int
    basis: Tuple[str, ...] = ()

    @property
    def health_ratio(self) -> float:
        if self.citizen_count <= 0:
            return 0.0
        return round(self.healthy_count / self.citizen_count, 4)

    def as_dict(self) -> Dict[str, object]:
        return {
            "overall": self.overall,
            "citizen_count": self.citizen_count,
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "unavailable_count": self.unavailable_count,
            "unknown_count": self.unknown_count,
            "health_ratio": self.health_ratio,
            "basis": list(self.basis),
        }


class EcosystemHealthAssessor:
    """Menilai kesehatan kolektif ekosistem (deterministik, read-only)."""

    def assess(self, healths: Dict[str, str],
               degraded_context: str = "") -> EcosystemHealthAssessment:
        """Agregasi health seluruh Citizen.

        `healths`: mapping identity_id -> health status.
        Agregasi: jika ADA yang unavailable, overall + pengaruhkannya;
        jika banyak degraded -> degraded; selain itu sesuai mayoritas.

        Deterministik: hasil hanya bergantung pada healths + degraded_context.
        """
        counts = {"healthy": 0, "degraded": 0, "unavailable": 0, "unknown": 0}
        for _cid, status in healths.items():
            lv = _health_level(status)
            counts[lv] = counts.get(lv, 0) + 1
        total = len(healths)

        overall = "unknown"
        if total > 0:
            if counts["unavailable"] > 0:
                overall = "degraded"
            elif counts["degraded"] >= counts["healthy"]:
                overall = "degraded"
            elif counts["healthy"] > 0 or counts["degraded"] > 0:
                overall = "healthy"
            else:
                overall = "unknown"

        basis = (
            "ecosystem health is collective assessment",
            "ecosystem health != runtime control",
            "deterministic aggregation",
        )
        return EcosystemHealthAssessment(
            overall=overall,
            citizen_count=total,
            healthy_count=counts["healthy"],
            degraded_count=counts["degraded"],
            unavailable_count=counts["unavailable"],
            unknown_count=counts["unknown"],
            basis=basis,
        )
