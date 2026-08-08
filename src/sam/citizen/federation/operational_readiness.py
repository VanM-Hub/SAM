# Federation Operational Model - WP-31
# IP-3.4-004 (AO-3.4-001, paket keempat - Federation Operational Coordination
# & Ecosystem Readiness)
#
# Model kesiapan operasional Federation - penilaian federation-wide readiness
# berdasarkan seluruh capability tersedia (foundation, trust, compatibility,
# collaboration, distributed intelligence), disatukan menjadi satu gambaran
# kesiapan operasional Federation.
#
# Guardrail IP-3.4-004:
#   Readiness != Execution (OR-01)
#   Aggregation != Authority (OR-04)
#   Federation Health != Runtime Control (OR-05)
#   Evidence-first readiness (OR-08)
#   Deterministic aggregation (OR-09)
#
# Output = assessment (readiness). BUKAN aksi. Federation memahami kesiapan
# kolektif; TIDAK pernah memulai kolaborasi otomatis.

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


# Jenis readiness yang dinilai per anggota Federation (sesuai evolusi
# capability IP-3.4-001..003)
READINESS_DIMENSIONS: Tuple[str, ...] = (
    "foundation",    # identity/registry/discovery (IP-3.4-001)
    "trust",         # trust evaluation (IP-3.4-002)
    "compatibility", # interop & compatibility (IP-3.4-002)
    "collaboration", # collaboration model (IP-3.4-003)
    "intelligence",  # distributed governance intelligence (IP-3.4-003)
)


@dataclass(frozen=True)
class FederationReadiness:
    """Readiness satu anggota Federation per dimensi (read-only, assessment).

    Seluruh nilai adalah penilaian (assessment), bukan aksi. Tidak ada
    atribut otoritas/perintah/eksekusi. Sovereignty anggota tetap lokal.
    """

    member_id: str
    dimension_scores: Tuple[float, ...] = ()   # selaras READINESS_DIMENSIONS
    overall: float = 0.0
    level: str = "unknown"                      # ready/partial/not-ready
    evidence: Tuple[str, ...] = ()

    def score(self, dimension: str) -> Optional[float]:
        """Skor readiness untuk satu dimensi (None bila dimensi tidak dikenal)."""
        if dimension not in READINESS_DIMENSIONS:
            return None
        idx = READINESS_DIMENSIONS.index(dimension)
        if idx >= len(self.dimension_scores):
            return None
        return self.dimension_scores[idx]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "member_id": self.member_id,
            "dimension_scores": {
                d: self.dimension_scores[READINESS_DIMENSIONS.index(d)]
                for d in READINESS_DIMENSIONS
                if READINESS_DIMENSIONS.index(d) < len(self.dimension_scores)
            },
            "overall": self.overall,
            "level": self.level,
            "evidence": list(self.evidence),
        }


def categorize_overall(overall: float) -> str:
    """Kategorikan skor readiness (0..1) menjadi level deterministik."""
    if overall >= 0.7:
        return "ready"
    if overall >= 0.4:
        return "partial"
    return "not-ready"


class FederationOperationalModel:
    """Membangun penilaian readiness satu anggota Federation (read-only).

    Readiness dihitung dari evidence capability anggota secara deterministik;
    hanya menilai, tidak mengubah state apa pun.
    """

    def assess(
        self,
        member_id: str,
        scores: Dict[str, float],
        evidence: Optional[Tuple[str, ...]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> FederationReadiness:
        """Nilai readiness anggota dari skor per dimensi (0..1).

        overall = rata-rata tertimbang skor dimensi (deterministik).
        Dimensi tanpa skor diabaikan dari pembagi (ketiadaan evidence tidak
        menurunkan tanpa dasar; hanya mengecualikan dari agregasi).
        """
        weighted_sum = 0.0
        weight_total = 0.0
        # daftar skor dimensi dengan panjang tetap (placeholder 0.0)
        ordered = [0.0] * len(READINESS_DIMENSIONS)
        for dim in READINESS_DIMENSIONS:
            s = scores.get(dim)
            if s is None:
                continue  # tidak ikut hitung; placeholder tetap 0.0
            w = (weights or {}).get(dim, 1.0)
            weighted_sum += max(0.0, min(1.0, float(s))) * w
            weight_total += w
            ordered[READINESS_DIMENSIONS.index(dim)] = \
                max(0.0, min(1.0, float(s)))

        overall = (weighted_sum / weight_total) if weight_total > 0 else 0.0
        return FederationReadiness(
            member_id=member_id,
            dimension_scores=tuple(ordered),
            overall=round(overall, 4),
            level=categorize_overall(overall),
            evidence=tuple(evidence or ()),
        )
