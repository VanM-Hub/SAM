# IP-3.6-A Production Governance - MISSION-3.6 (AO-ENG-001)
# WP-A1 (Production Governance Profile) + WP-A2 (Operational Policy Validation)
# + WP-A3 (Governance Readiness) + WP-A4 (Operational Compliance)
# + WP-A5 (Governance Baseline Verification).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail MISSION-3.6: Production Governance MEASURES & REPORTS readiness;
#   ia TIDAK mengeksekusi/menerapkan governance. Profil governance DIBERIKAN
#   dari luar sebagai input; platform membaca & memverifikasi secara
#   deterministik.

"""Production Governance (Track A).

Menilai kesiapan operasional governance sebagai an input-driven, read-only
verification layer. Menyusun Production Governance Profile, memvalidasi
policy operasional, menilai governance readiness, memeriksa operational
compliance, dan memverifikasi baseline governance.

Seluruh fungsi deterministik & immutable; tidak ada efek samping eksekusi.
"""

from dataclasses import dataclass, field
from typing import Dict, Sequence, Tuple, Optional


# --- WP-A1 Production Governance Profile ------------------------------------

@dataclass(frozen=True)
class GovernanceProfile:
    """Profil governance produksi (standardized labels, read-only).

    Menyediakan label/urutan deterministik untuk elemen governance yang
    diperiksa. Nilai dibangun dari konstanta (bukan runtime state).
    """

    governance_areas: Tuple[str, ...] = ("decision", "policy", "audit", "accountability")
    operational_states: Tuple[str, ...] = ("ready", "degraded", "blocked")
    evidence_statuses: Tuple[str, ...] = ("present", "missing", "stale")

    @property
    def label_set(self) -> Tuple[str, ...]:
        """Seluruh label governance (gabungan deterministik, dedup)."""
        seen = []
        for area in self.governance_areas:
            if area not in seen:
                seen.append(area)
        return tuple(seen)


@dataclass(frozen=True)
class GovernanceProfileStatus:
    """Status profil governance yang diukur (immutable).

    Dihitung dari input capabilities; TIDAK memegang keputusan.
    """

    areas_covered: Tuple[str, ...] = ()
    states_observed: Tuple[str, ...] = ()
    profile_ok: bool = True


def assess_governance_profile(
    profile: GovernanceProfile,
    covered_areas: Sequence[str],
    states: Sequence[str],
) -> GovernanceProfileStatus:
    """Buat status profil dari area yang tercakup & state teramati.

    Deterministik: hasil bergantung penuh pada input.
    """
    covered = tuple(sorted(set(str(a) for a in covered_areas)))
    observed = tuple(sorted(set(str(s) for s in states)))
    # profil dianggap ok bila seluruh area standar tercakup minimal 1x
    missing = [a for a in profile.governance_areas if a not in covered]
    return GovernanceProfileStatus(
        areas_covered=covered,
        states_observed=observed,
        profile_ok=not missing,
    )


# --- WP-A2 Operational Policy Validation -------------------------------------

@dataclass(frozen=True)
class PolicyEntry:
    """Satu policy operasional yang diberikan (input)."""

    policy_id: str
    description: str = ""
    enforced: bool = False

    def validated(self) -> bool:
        """Policy valid bila memiliki id dan ditandai enforced."""
        return bool(self.policy_id) and self.enforced


@dataclass(frozen=True)
class PolicyValidationResult:
    """Hasil validasi policy operasional (read-only)."""

    valid_count: int = 0
    invalid_ids: Tuple[str, ...] = ()

    @property
    def all_valid(self) -> bool:
        return self.invalid_ids == ()


def validate_operational_policies(
    policies: Sequence[PolicyEntry],
) -> PolicyValidationResult:
    """Validasi seluruh policy; kumpulkan yang tidak valid (deterministik)."""
    invalid = tuple(
        p.policy_id for p in policies if not p.validated()
    )
    return PolicyValidationResult(
        valid_count=sum(1 for p in policies if p.validated()),
        invalid_ids=invalid,
    )


# --- WP-A3 Governance Readiness ----------------------------------------------

@dataclass(frozen=True)
class ReadinessInput:
    """Input readiness governance (dari capability), nilai 0..1."""

    governance_coverage: float = 0.0
    policy_coverage: float = 0.0
    evidence_coverage: float = 0.0

    def _clamp(self, v: float) -> float:
        return max(0.0, min(1.0, float(v)))


@dataclass(frozen=True)
class GovernanceReadiness:
    """Penilaian readiness governance (deterministik, read-only)."""

    governance: float
    policy: float
    evidence: float

    @property
    def overall(self) -> float:
        return round((self.governance + self.policy + self.evidence) / 3.0, 4)

    @property
    def ready(self) -> bool:
        return self.overall >= 0.7


def assess_readiness(input: ReadinessInput) -> GovernanceReadiness:
    """Hitung readiness governance dari input (deterministik)."""
    return GovernanceReadiness(
        governance=input._clamp(getattr(input, "governance_coverage")),
        policy=input._clamp(getattr(input, "policy_coverage")),
        evidence=input._clamp(getattr(input, "evidence_coverage")),
    )


# --- WP-A4 Operational Compliance --------------------------------------------

@dataclass(frozen=True)
class ComplianceCheckItem:
    """Satu item compliance operasional (input)."""

    check_id: str
    passed: bool = False


def operational_compliance_score(
    items: Sequence[ComplianceCheckItem],
) -> Tuple[int, int, float]:
    """Skor compliance operasional: (passed, total, ratio). Deterministik."""
    passed = sum(1 for i in items if i.passed)
    total = len(items)
    ratio = round(passed / total, 4) if total else 1.0
    return (passed, total, ratio)


# --- WP-A5 Governance Baseline Verification ----------------------------------

@dataclass(frozen=True)
class BaselineEntry:
    """Satu entri baseline governance (nilai yang diharapkan)."""

    key: str
    expected: str
    actual: Optional[str] = None

    @property
    def matches(self) -> bool:
        return self.actual is not None and self.actual == self.expected


@dataclass(frozen=True)
class BaselineVerification:
    """Hasil verifikasi baseline governance (read-only)."""

    matched: Tuple[str, ...] = ()
    mismatched: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.mismatched == ()


def verify_governance_baseline(
    entries: Sequence[BaselineEntry],
) -> BaselineVerification:
    """Verifikasi baseline; pisahkan matched vs mismatched (deterministik)."""
    matched = tuple(e.key for e in entries if e.matches)
    mismatched = tuple(e.key for e in entries if not e.matches)
    return BaselineVerification(matched=matched, mismatched=mismatched)
