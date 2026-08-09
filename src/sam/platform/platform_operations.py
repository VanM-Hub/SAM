# IP-3.6-B Platform Operations - MISSION-3.6 (AO-ENG-001)
# WP-B1 (Deployment Validation) + WP-B2 (Environment Validation)
# + WP-B3 (Operational Configuration) + WP-B4 (Startup Verification)
# + WP-B5 (Shutdown Verification).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail MISSION-3.6: Platform Operations VERIFIES & REPORTS deployment/
#   environment/config/startup/shutdown readiness. Ia TIDAK melakukan
#   deployment, mengubah environment, atau mengeksekusi start/stop nyata.
#   Seluruh pengamatan diberikan sebagai input; verifikasi deterministik.

"""Platform Operations (Track B).

Lapisan verifikasi read-only untuk kesiapan operasional platform: deployment,
environment, konfigurasi operasional, startup, dan shutdown. Menerima hasil
inspeksi dari luar dan menghasilkan verifikasi deterministik beserta
rekomendasi lintasan (path) - tanpa efek samping.

Verification (bukan execution): tidak melakukan deploy/start/stop itu sendiri.
"""

from dataclasses import dataclass
from typing import Sequence, Tuple


# --- WP-B1 Deployment Validation ---------------------------------------------

@dataclass(frozen=True)
class DeploymentArtifact:
    """Satu artefak deployment yang diinspeksi (input)."""

    artifact_id: str
    present: bool = False
    version: str = ""


@dataclass(frozen=True)
class DeploymentValidation:
    """Hasil validasi deployment (read-only)."""

    present_ids: Tuple[str, ...] = ()
    missing_ids: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.missing_ids == ()


def validate_deployment(
    artifacts: Sequence[DeploymentArtifact],
) -> DeploymentValidation:
    """Validasi artefak deployment; pisahkan present vs missing."""
    present = tuple(a.artifact_id for a in artifacts if a.present)
    missing = tuple(a.artifact_id for a in artifacts if not a.present)
    return DeploymentValidation(present_ids=present, missing_ids=missing)


# --- WP-B2 Environment Validation --------------------------------------------

@dataclass(frozen=True)
class EnvironmentFactor:
    """Satu faktor environment yang diinspeksi (input)."""

    name: str
    satisfied: bool = False


@dataclass(frozen=True)
class EnvironmentValidation:
    """Hasil validasi environment (read-only)."""

    satisfied: Tuple[str, ...] = ()
    unsatisfied: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.unsatisfied == ()


def validate_environment(
    factors: Sequence[EnvironmentFactor],
) -> EnvironmentValidation:
    """Validasi faktor environment; pisahkan satisfied vs unsatisfied."""
    satisfied = tuple(f.name for f in factors if f.satisfied)
    unsatisfied = tuple(f.name for f in factors if not f.satisfied)
    return EnvironmentValidation(satisfied=satisfied, unsatisfied=unsatisfied)


# --- WP-B3 Operational Configuration -----------------------------------------

@dataclass(frozen=True)
class ConfigSetting:
    """Satu pengaturan konfigurasi operasional yang diinspeksi (input)."""

    key: str
    expected: str
    actual: str = ""


@dataclass(frozen=True)
class ConfigVerification:
    """Hasil verifikasi konfigurasi (read-only)."""

    aligned: Tuple[str, ...] = ()
    misaligned: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.misaligned == ()


def verify_configuration(
    settings: Sequence[ConfigSetting],
) -> ConfigVerification:
    """Verifikasi konfigurasi terhadap harapan; pisahkan aligned/misaligned."""
    aligned = tuple(s.key for s in settings if s.actual == s.expected)
    misaligned = tuple(s.key for s in settings if s.actual != s.expected)
    return ConfigVerification(aligned=aligned, misaligned=misaligned)


# --- WP-B4 Startup Verification ----------------------------------------------

@dataclass(frozen=True)
class StartupCheck:
    """Satu cek startup yang diinspeksi (input)."""

    check_id: str
    passed: bool = False


@dataclass(frozen=True)
class StartupVerification:
    """Hasil verifikasi startup (read-only)."""

    passed_checks: Tuple[str, ...] = ()
    failed_checks: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.failed_checks == ()


def verify_startup(
    checks: Sequence[StartupCheck],
) -> StartupVerification:
    """Verifikasi cek startup; pisahkan passed vs failed."""
    passed = tuple(c.check_id for c in checks if c.passed)
    failed = tuple(c.check_id for c in checks if not c.passed)
    return StartupVerification(passed_checks=passed, failed_checks=failed)


# --- WP-B5 Shutdown Verification ---------------------------------------------

@dataclass(frozen=True)
class ShutdownCheck:
    """Satu cek shutdown yang diinspeksi (input)."""

    check_id: str
    completed: bool = False


@dataclass(frozen=True)
class ShutdownVerification:
    """Hasil verifikasi shutdown (read-only)."""

    completed: Tuple[str, ...] = ()
    incomplete: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.incomplete == ()


def verify_shutdown(
    checks: Sequence[ShutdownCheck],
) -> ShutdownVerification:
    """Verifikasi cek shutdown; pisahkan completed vs incomplete."""
    completed = tuple(c.check_id for c in checks if c.completed)
    incomplete = tuple(c.check_id for c in checks if not c.completed)
    return ShutdownVerification(completed=completed, incomplete=incomplete)
