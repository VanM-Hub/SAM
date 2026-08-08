# Federation Trust Model - WP-11
# IP-3.4-002 (AO-3.4-001 / ED-3.4-001, paket kedua)
#
# Model immutable trust antar Federation Member.
#
# Guardrail IP-3.4-002:
#   Trust != Authority  - trust hanya assessment, TIDAK memberikan kewenangan
#   Evidence-first      - seluruh trust dapat dijelaskan oleh evidence
#   Deterministic       - input identik -> output identik
#
# Trust adalah HASIL ASSESSMENT, bukan hak istimewa (privilege).
# FederationTrustProfile tidak memberdayakan siapapun untuk bertindak;
# ia hanya merekam tingkat kepercayaan berdasarkan bukti.

from dataclasses import dataclass
from typing import Any, Dict, Tuple

# level trust (rendah -> tinggi)
_TRUST_LEVELS = ("unknown", "low", "medium", "high")


def _trust_rank(level: str) -> int:
    lvl = level.strip().lower()
    if lvl not in _TRUST_LEVELS:
        return 0  # unknown
    return _TRUST_LEVELS.index(lvl)


@dataclass(frozen=True)
class TrustLevel:
    """Tingkat kepercayaan (assessment, bukan otoritas)."""

    level: str = "unknown"

    def __post_init__(self) -> None:
        lvl = self.level.strip().lower()
        if lvl not in _TRUST_LEVELS:
            lvl = "unknown"
        object.__setattr__(self, "level", lvl)

    @property
    def rank(self) -> int:
        return _trust_rank(self.level)

    def __lt__(self, other: "TrustLevel") -> bool:
        return self.rank < other.rank

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TrustLevel):
            return self.level == other.level
        return NotImplemented

    def as_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "rank": self.rank}


@dataclass(frozen=True)
class TrustEvidence:
    """Satu bukti yang mendukung penilaian trust.

    kind: certification | compatibility | contract | health | evidence
    source: id member/sumber bukti
    detail: deskripsi ringkas
    """

    kind: str
    source: str
    detail: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class TrustConstraint:
    """Kendala yang membatasi trust (e.g. kompatibilitas belum penuh)."""

    name: str
    detail: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "detail": self.detail}


@dataclass(frozen=True)
class FederationTrustProfile:
    """Profil trust satu member Federation (hasil assessment, read-only)."""

    member_id: str
    level: TrustLevel = TrustLevel()
    evidence: Tuple[TrustEvidence, ...] = ()
    constraints: Tuple[TrustConstraint, ...] = ()

    def __post_init__(self) -> None:
        # deterministik: sortir bukti & kendala
        if not isinstance(self.level, TrustLevel):
            object.__setattr__(self, "level", TrustLevel(str(self.level)))
        ev = tuple(sorted(self.evidence, key=lambda e: (e.kind, e.source)))
        cs = tuple(sorted(self.constraints, key=lambda c: c.name))
        object.__setattr__(self, "evidence", ev)
        object.__setattr__(self, "constraints", cs)

    @property
    def is_trusted(self) -> bool:
        """Trust assessment (>= high). BUKAN approval, TIDAK memberi kuasa."""
        return _trust_rank(self.level.level) >= _trust_rank("high")

    def evidence_kinds(self) -> Tuple[str, ...]:
        return tuple(sorted({e.kind for e in self.evidence}))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "member_id": self.member_id,
            "level": self.level.as_dict(),
            "is_trusted": self.is_trusted,
            "evidence": [e.as_dict() for e in self.evidence],
            "constraints": [c.as_dict() for c in self.constraints],
        }
