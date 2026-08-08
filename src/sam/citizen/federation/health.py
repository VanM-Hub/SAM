# Federation Health - WP-06
# IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
#
# Health seluruh Federation Member - OBSERVASIONAL.
#
# Federation Health != Monitoring Control: Federation hanya MENGAMATI
# status yang diumumkan member, TIDAK mengontrol/memperbaiki/memulai-ulang
# node remote. Hasilnya agregat observasi yang deterministik.

from dataclasses import dataclass
from typing import Dict, Tuple

_HEALTH_STATES = ("healthy", "degraded", "unavailable", "unknown")


def _health_normalized(state: str) -> str:
    s = state.strip().lower()
    return s if s in _HEALTH_STATES else "unknown"


@dataclass(frozen=True)
class FederationHealth:
    """Agregat observasional health seluruh member Federation."""

    member_health: Tuple[Tuple[str, str], ...] = ()
    overall: str = "unknown"

    def __post_init__(self) -> None:
        normalized = tuple(
            (m, _health_normalized(h)) for m, h in self.member_health
        )
        normalized = tuple(sorted(normalized, key=lambda x: x[0]))
        object.__setattr__(self, "member_health", normalized)
        overall = self._aggregate(normalized)
        object.__setattr__(self, "overall", overall)

    @staticmethod
    def _aggregate(member_health) -> str:
        if not member_health:
            return "unknown"
        states = [h for _, h in member_health]
        if "unavailable" in states:
            return "degraded"
        if "degraded" in states:
            return "degraded"
        if all(s == "healthy" for s in states):
            return "healthy"
        return "unknown"

    def as_dict(self) -> Dict[str, object]:
        return {
            "overall": self.overall,
            "member_health": list(self.member_health),
        }

    @property
    def healthy_count(self) -> int:
        return sum(1 for _, h in self.member_health if h == "healthy")

    @property
    def degraded_count(self) -> int:
        return sum(1 for _, h in self.member_health if h == "degraded")

    @property
    def unavailable_count(self) -> int:
        return sum(1 for _, h in self.member_health if h == "unavailable")


class FederationHealthAssessor:
    """Pengamati health Federation (observasi agregat, tanpa kontrol)."""

    def assess(self, health: Dict[str, str]) -> FederationHealth:
        """Agregasi status yang DIUMUMKAN member ke penilaian kolektif."""
        return FederationHealth(member_health=tuple(sorted(health.items())))
