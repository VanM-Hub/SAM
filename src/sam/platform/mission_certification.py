# IP-3.6-E Mission Certification - MISSION-3.6 (AO-ENG-001)
# WP-E1 (End-to-End Production Certification) + WP-E2 (Mission Readiness
# Assessment) + WP-E3 (Operational Regression) + WP-E4 (Compliance
# Regression) + WP-E5 (Mission Engineering Report).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail MISSION-3.6: Mission Certification AGGREGATES hasil seluruh
#   track (A..D) menjadi penilaian readiness & rekomendasi engineering.
#   Ini alat verifikasi/penilaian read-only; bukan otoritas arsitektur.

"""Mission Certification (Track E).

Menilai kesiapan produksi MISSION-3.6 secara end-to-end dari hasil track
A..D, menguji operasional & compliance regression, dan menyusun bahan
Mission Engineering Report. Read-only & deterministic; rekomendasi bersifat
engineering (bukan keputusan architecture).

Assessment (bukan authority): menyajikan evidence, tidak memutuskan.
"""

from dataclasses import dataclass
from typing import Sequence, Tuple, Optional


# --- WP-E1 End-to-End Production Certification -------------------------------

@dataclass(frozen=True)
class TrackResult:
    """Hasil satu track MISSION-3.6 (input)."""

    track: str
    ok: bool = False


@dataclass(frozen=True)
class ProductionCertification:
    """Sertifikasi produksi end-to-end (read-only)."""

    passed_tracks: Tuple[str, ...] = ()
    failed_tracks: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.failed_tracks == ()

    @property
    def ratio(self) -> float:
        total = len(self.passed_tracks) + len(self.failed_tracks)
        return (round(len(self.passed_tracks) / total, 4) if total else 1.0)


def certify_end_to_end(
    track_results: Sequence[TrackResult],
) -> ProductionCertification:
    """Susun sertifikasi produksi dari hasil track (deterministik)."""
    passed = tuple(t.track for t in track_results if t.ok)
    failed = tuple(t.track for t in track_results if not t.ok)
    return ProductionCertification(passed_tracks=passed, failed_tracks=failed)


# --- WP-E2 Mission Readiness Assessment --------------------------------------

@dataclass(frozen=True)
class ReadinessGate:
    """Satu gate kesiapan misi (input)."""

    gate_id: str
    met: bool = False


@dataclass(frozen=True)
class MissionReadiness:
    """Penilaian kesiapan misi (read-only)."""

    met_gates: Tuple[str, ...] = ()
    unmet_gates: Tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.unmet_gates == ()

    @property
    def score(self) -> float:
        total = len(self.met_gates) + len(self.unmet_gates)
        return (round(len(self.met_gates) / total, 4) if total else 1.0)


def assess_mission_readiness(
    gates: Sequence[ReadinessGate],
) -> MissionReadiness:
    """Pisahkan gate kesiapan met vs unmet (deterministik)."""
    met = tuple(g.gate_id for g in gates if g.met)
    unmet = tuple(g.gate_id for g in gates if not g.met)
    return MissionReadiness(met_gates=met, unmet_gates=unmet)


# --- WP-E3 Operational Regression --------------------------------------------

@dataclass(frozen=True)
class RegressionSuite:
    """Hasil satu suite regression operasional (input)."""

    suite: str
    passed: bool = False
    count: int = 0


@dataclass(frozen=True)
class OperationalRegression:
    """Hasil regression operasional (read-only)."""

    failed_suites: Tuple[str, ...] = ()
    total_cases: int = 0

    @property
    def ok(self) -> bool:
        return self.failed_suites == ()


def run_operational_regression(
    suites: Sequence[RegressionSuite],
) -> OperationalRegression:
    """Agregasi hasil regression; kumpulkan suite yang gagal."""
    failed = tuple(s.suite for s in suites if not s.passed)
    total = sum(int(s.count) for s in suites)
    return OperationalRegression(failed_suites=failed, total_cases=total)


# --- WP-E4 Compliance Regression ---------------------------------------------

@dataclass(frozen=True)
class ComplianceGroup:
    """Hasil satu group compliance (input)."""

    group: str
    passed: bool = False


@dataclass(frozen=True)
class ComplianceRegression:
    """Hasil regression compliance (read-only)."""

    failed_groups: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.failed_groups == ()


def run_compliance_regression(
    groups: Sequence[ComplianceGroup],
) -> ComplianceRegression:
    """Agregasi hasil compliance; kumpulkan group yang gagal."""
    failed = tuple(g.group for g in groups if not g.passed)
    return ComplianceRegression(failed_groups=failed)


# --- WP-E5 Mission Engineering Report (bahan) --------------------------------

@dataclass(frozen=True)
class ReportSection:
    """Satu seksi dalam Mission Engineering Report (bahan)."""

    title: str
    verified: bool = False
    notes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class MissionEngineeringReport:
    """Rekomendasi engineering final MISSION-3.6 (read-only).

    Menyusun ringkasan seluruh track + rekomendasi engineering. Ini artefak
    formal utk Architecture Acceptance tingkat Mission (AO-ENG-001).
    """

    sections: Tuple[ReportSection, ...] = ()
    recommendation: str = ""

    @property
    def all_verified(self) -> bool:
        return all(s.verified for s in self.sections)

    def section_titles(self) -> Tuple[str, ...]:
        return tuple(s.title for s in self.sections)


def build_engineering_report(
    sections: Sequence[ReportSection],
    recommendation: str,
) -> MissionEngineeringReport:
    """Susun bahan Mission Engineering Report (deterministik, immutable)."""
    return MissionEngineeringReport(
        sections=tuple(sections),
        recommendation=recommendation,
    )
