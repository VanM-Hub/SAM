# Citizen Certification Model - WP-21
# IP-3.3-003 (AO-3.3-001 / ED-3.3-001 cycle 3)
#
# Model sertifikasi, maturity, dan status kepatuhan Citizen. Menduniakan
# "seberapa siap / seberapa patuh" seorang Citizen TANPA pernah 'approve'
# atau mengubah statusnya (Certification != Approval; Certification !=
# Lifecycle Mutation).
#
# Murni representasi data (DTO), immutable, deterministik.

import hashlib
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Tingkat maturity Citizen - deskriptif, bukan otorisasi.
_MATURITY_LEVELS = (
    "unassessed",   # belum dinilai
    "initial",      # teridentifikasi
    "defined",      # terdeskripsikan
    "capable",      # punya capability
    "certified",    # lulus assessment
)


def _maturity_normalized(level: str) -> str:
    """Normalisasi level maturity -> lower-case konsisten, default 'unassessed'."""
    lv = level.strip().lower()
    return lv if lv in _MATURITY_LEVELS else "unassessed"


# Status kepatuhan - hasil penilaian, bukan keputusan otoritas.
_COMPLIANCE_STATUS = ("noncompliant", "partial", "compliant")


def _compliance_normalized(status: str) -> str:
    st = status.strip().lower()
    return st if st in _COMPLIANCE_STATUS else "noncompliant"


@dataclass(frozen=True)
class CertificationResult:
    """Hasil sertifikasi seorang Citizen (immutable, evidence-first).

    - certification_id: deterministik (sha1 dari identity + peringkat).
    - maturity: level maturity yang dinilai.
    - compliance: status kepatuhan (noncompliant/partial/compliant).
    - checks_passed / checks_total: proporsi kepatuhan.
    - evidence: jejak bukti yang mendukung hasil.
    - qualified: apakah citizen memenuhi ambang maturity & compliance.
    - Note: 'qualified' BUKAN persetujuan hidupkan citizen.
    """

    certification_id: str
    citizen_identity_id: str
    maturity: str
    compliance: str
    checks_passed: int
    checks_total: int
    evidence: Tuple[str, ...] = ()
    basis: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "citizen_identity_id",
                           self.citizen_identity_id.strip())
        object.__setattr__(self, "maturity",
                           _maturity_normalized(self.maturity))
        object.__setattr__(self, "compliance",
                           _compliance_normalized(self.compliance))
        object.__setattr__(self, "checks_passed", max(0, self.checks_passed))
        object.__setattr__(self, "checks_total", max(0, self.checks_total))
        object.__setattr__(self, "evidence", tuple(self.evidence))

    @property
    def compliance_ratio(self) -> float:
        if self.checks_total <= 0:
            return 0.0
        return round(self.checks_passed / self.checks_total, 4)

    @property
    def qualified(self) -> bool:
        """Apakah citizen layak dianggap 'certified' level.

        Estimator deterministik; TIDAK mengubah status apapun.
        """
        maturity_ok = self.maturity in ("capable", "certified")
        compliance_ok = self.compliance in ("compliant", "partial")
        return maturity_ok and compliance_ok

    def as_dict(self) -> Dict[str, object]:
        return {
            "certification_id": self.certification_id,
            "citizen_identity_id": self.citizen_identity_id,
            "maturity": self.maturity,
            "compliance": self.compliance,
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
            "compliance_ratio": self.compliance_ratio,
            "qualified": self.qualified,
            "evidence": list(self.evidence),
            "basis": list(self.basis),
        }

    @classmethod
    def new(cls, citizen_identity_id: str, maturity: str,
            compliance: str, checks_passed: int, checks_total: int, *,
            evidence: Tuple[str, ...] = (),
            basis: Tuple[str, ...] = ()) -> "CertificationResult":
        digest = hashlib.sha1(
            (citizen_identity_id + "|" + maturity.strip().lower()).encode("utf-8")
        ).hexdigest()[:12]
        return cls(
            certification_id="cert-" + digest,
            citizen_identity_id=citizen_identity_id,
            maturity=_maturity_normalized(maturity),
            compliance=_compliance_normalized(compliance),
            checks_passed=checks_passed,
            checks_total=checks_total,
            evidence=tuple(evidence),
            basis=tuple(basis) + ("certification != approval",
                                  "deterministic id"),
        )


@dataclass(frozen=True)
class CitizenMaturityProfile:
    """Profil maturity seorang Citizen (immutable)."""

    citizen_identity_id: str
    maturity: str
    assessed_at_basis: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "citizen_identity_id",
                           self.citizen_identity_id.strip())
        object.__setattr__(self, "maturity",
                           _maturity_normalized(self.maturity))

    def as_dict(self) -> Dict[str, object]:
        return {
            "citizen_identity_id": self.citizen_identity_id,
            "maturity": self.maturity,
            "assessed_at_basis": list(self.assessed_at_basis),
            "notes": list(self.notes),
        }

    def is_mature_enough(self, threshold: str = "capable") -> bool:
        th = _maturity_normalized(threshold)
        order = _MATURITY_LEVELS
        return order.index(self.maturity) >= order.index(th)


_MATURITY_LEVELS_PUBLIC = tuple(list(_MATURITY_LEVELS))
