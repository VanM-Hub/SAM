# Citizen Health Model - WP-06
# IP-3.3-001 (AO-3.3-001 / ED-3.3-001)
#
# Model kesehatan citizen (status & deterministik). Health adalah OBSERVASI,
# bukan keputusan: citizen TIDAK diaktifkan/dimatikan/di-restart di sini.
# Registry/analyzer hanya MENILAI kesehatan (read-only).

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# status kesehatan yang dikenal (konsisten, equal untuk semua kind).
_HEALTH_LEVELS = ("healthy", "degraded", "unavailable", "unknown")


@dataclass(frozen=True)
class CitizenHealth:
    """Status kesehatan seorang citizen (immutable).

    level     : healthy/degraded/unavailable/unknown
    checks    : daftar hasil cek (tuple[str]) - bukti observasi
    basis     : alasan level ini diambil (explainable)
    """

    identity_id: str
    level: str = "unknown"
    checks: Tuple[str, ...] = ()
    basis: Tuple[str, ...] = ()
    observed_at: str = ""

    def __post_init__(self) -> None:
        lvl = self.level.strip().lower()
        if lvl not in _HEALTH_LEVELS:
            lvl = "unknown"
        object.__setattr__(self, "level", lvl)

    @property
    def is_available(self) -> bool:
        """Citizen tersedia bila sehat atau terdegradasi (bukan unavailable)."""
        return self.level != "unavailable"

    def as_dict(self) -> Dict[str, object]:
        return {
            "identity_id": self.identity_id,
            "level": self.level,
            "checks": list(self.checks),
            "basis": list(self.basis),
            "observed_at": self.observed_at,
        }


class CitizenHealthAnalyzer:
    """Menilai kesehatan citizen dari hasil check yang diberikan.

    Murni agregasi deterministik: bila ada check 'unavailable' -> unavailable;
    bila ada check 'degraded' -> degraded; bila semua 'healthy' -> healthy.
    Tidak ada eksekusi, tidak ada restart, tidak ada mutation.
    """

    def analyze(self, identity_id: str, checks: Tuple[str, ...],
                observed_at: str = "") -> CitizenHealth:
        if not checks:
            return CitizenHealth(identity_id=identity_id, level="unknown",
                                 checks=checks, observed_at=observed_at)
        if "unavailable" in checks:
            level = "unavailable"
        elif "degraded" in checks:
            level = "degraded"
        else:
            level = "healthy"
        basis = ("health is observation",
                 "deterministic aggregation of {} checks".format(len(checks)))
        return CitizenHealth(identity_id=identity_id, level=level,
                             checks=checks, basis=basis, observed_at=observed_at)
