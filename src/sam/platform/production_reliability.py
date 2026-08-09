# IP-3.6-D Production Reliability - MISSION-3.6 (AO-ENG-001)
# WP-D1 (Reliability Verification) + WP-D2 (Recoverability Validation)
# + WP-D3 (Operational Stability) + WP-D4 (Production Diagnostics)
# + WP-D5 (Long-running Verification).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail MISSION-3.6: Production Reliability VERIFIES & DIAGNOSES
#   reliability/recoverability/stability secara deterministik dari input
#   pengamatan. Ia TIDAK menjalankan recovery, memicu failover, atau
#   mengubah runtime. Diagnosis bebas efek samping.

"""Production Reliability (Track D).

Verifikasi read-only untuk keandalan produksi: reliability,
recoverability, stability, diagnostics, dan long-running. Menerima hasil
pengamatan (uptime, retry, recovery plan, dsb.) sebagai input dan menghasilkan
penilaian deterministik. Tidak menjalankan recovery/failover apa pun.

Verification (bukan intervention): mendiagnosis, tidak mengobati.
"""

from dataclasses import dataclass
from typing import Sequence, Tuple, Optional


# --- WP-D1 Reliability Verification ------------------------------------------

@dataclass(frozen=True)
class ReliabilityObservation:
    """Satu pengamatan keandalan (input)."""

    component: str
    attempts: int = 0
    successes: int = 0

    @property
    def success_rate(self) -> float:
        return (round(self.successes / self.attempts, 4)
                if self.attempts else 0.0)


@dataclass(frozen=True)
class ReliabilityVerification:
    """Hasil verifikasi keandalan (read-only)."""

    reliable: Tuple[str, ...] = ()
    degraded: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.degraded == ()


def verify_reliability(
    observations: Sequence[ReliabilityObservation],
    threshold: float = 0.9,
) -> ReliabilityVerification:
    """Verifikasi keandalan per komponen terhadap ambang (deterministik)."""
    reliable = tuple(o.component for o in observations
                     if o.success_rate >= threshold)
    degraded = tuple(o.component for o in observations
                     if o.success_rate < threshold)
    return ReliabilityVerification(reliable=reliable, degraded=degraded)


# --- WP-D2 Recoverability Validation -----------------------------------------

@dataclass(frozen=True)
class RecoveryPlanPiece:
    """Sebuah potongan rencana pemulihan yang dinilai (input)."""

    step: str
    available: bool = False


@dataclass(frozen=True)
class RecoverabilityValidation:
    """Hasil validasi recoverability (read-only)."""

    available: Tuple[str, ...] = ()
    unavailable: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.unavailable == ()


def validate_recoverability(
    pieces: Sequence[RecoveryPlanPiece],
) -> RecoverabilityValidation:
    """Validasi recoverability; pisahkan available vs unavailable."""
    available = tuple(p.step for p in pieces if p.available)
    unavailable = tuple(p.step for p in pieces if not p.available)
    return RecoverabilityValidation(available=available, unavailable=unavailable)


# --- WP-D3 Operational Stability ---------------------------------------------

@dataclass(frozen=True)
class StabilitySample:
    """Satu sampel kestabilan operasional (input)."""

    period: str
    stable: bool = False


@dataclass(frozen=True)
class StabilityAssessment:
    """Penilaian kestabilan (read-only)."""

    stable_periods: Tuple[str, ...] = ()
    unstable_periods: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.unstable_periods == ()


def assess_stability(
    samples: Sequence[StabilitySample],
) -> StabilityAssessment:
    """Pisahkan periode stabil vs tidak stabil (deterministik)."""
    stable = tuple(s.period for s in samples if s.stable)
    unstable = tuple(s.period for s in samples if not s.stable)
    return StabilityAssessment(stable_periods=stable, unstable_periods=unstable)


# --- WP-D4 Production Diagnostics --------------------------------------------

@dataclass(frozen=True)
class DiagnosticFinding:
    """Satu temuan diagnostik (input)."""

    finding_id: str
    severity: str = "info"  # info | warning | critical

    @property
    def is_critical(self) -> bool:
        return self.severity == "critical"


@dataclass(frozen=True)
class DiagnosticsSummary:
    """Ringkasan diagnostik (read-only)."""

    critical: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    info_findings: Tuple[str, ...] = ()

    @property
    def has_critical(self) -> bool:
        return bool(self.critical)


def summarize_diagnostics(
    findings: Sequence[DiagnosticFinding],
) -> DiagnosticsSummary:
    """Kelompokkan temuan diagnostik per severity (deterministik)."""
    critical = tuple(f.finding_id for f in findings if f.severity == "critical")
    warnings = tuple(f.finding_id for f in findings if f.severity == "warning")
    info = tuple(f.finding_id for f in findings if f.severity == "info")
    return DiagnosticsSummary(critical=critical, warnings=warnings, info_findings=info)


# --- WP-D5 Long-running Verification -----------------------------------------

@dataclass(frozen=True)
class LongRunningObservation:
    """Satu observasi long-running platform (input)."""

    session_id: str
    duration_hours: float = 0.0
    ok: bool = False


@dataclass(frozen=True)
class LongRunningVerification:
    """Hasil verifikasi long-running (read-only)."""

    sessions_ok: int = 0
    sessions_degraded: int = 0
    total_duration_hours: float = 0.0

    @property
    def ok(self) -> bool:
        return self.sessions_degraded == 0


def verify_long_running(
    observations: Sequence[LongRunningObservation],
) -> LongRunningVerification:
    """Verifikasi long-running; agregasi session sehat vs menurun."""
    ok = sum(1 for o in observations if o.ok)
    degraded = len(observations) - ok
    total_duration = round(sum(float(o.duration_hours) for o in observations), 4)
    return LongRunningVerification(
        sessions_ok=ok,
        sessions_degraded=degraded,
        total_duration_hours=total_duration,
    )
