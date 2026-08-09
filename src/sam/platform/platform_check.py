# Platform Check (Integration Gate) - IP-3.5-005 (AO-ENG-001)
# WP-30 (Regression) + WP-31 (Compliance) + WP-32 (Certification)
# + WP-33 (Production Readiness).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail: seluruh gate bersifat read-only & deterministic. Platform
#   ENGINEERING verification (bukan Architecture Review - per AO-ENG-001
#   internal deliverable).

"""Platform Check (Engineering Verification Gate).

Menyediakan gate verifikasi integrasi platform: regression, compliance,
certification, dan production readiness. Seluruh pemeriksaan deterministik
& read-only; ini alat verifikasi engineering, bukan otoritas arsitektur.
"""

from dataclasses import dataclass
from typing import Sequence, Tuple, Optional

from sam.platform.compliance import (
    compliance_check,
    mission_compliance_check,
    citizen_compliance_check,
    explainability_compliance_check,
)


@dataclass(frozen=True)
class GateResult:
    """Hasil satu gate verifikasi (immutable)."""

    name: str
    ok: bool
    details: Tuple[str, ...] = ()

    @property
    def verdict(self) -> str:
        return "PASS" if self.ok else "FAIL"


# --- WP-31 Compliance gate ---------------------------------------------------

def _compliance_gates() -> Tuple[str, ...]:
    """Jalankan seluruh compliance platform; kembalikan pesan kekurangan."""
    failures = []
    for name, fn in (
        ("PEX (Platform Workspace)", compliance_check),
        ("MEX (Mission Experience)", mission_compliance_check),
        ("CX (Citizen Experience)", citizen_compliance_check),
        ("EX (Explainability Experience)", explainability_compliance_check),
    ):
        res = fn()
        if not res.ok:
            failures.append("%s: %s" % (name, "; ".join(res.messages)))
    return tuple(failures)


# --- WP-30 Regression gate ---------------------------------------------------

def regression_gate(
    test_results: Sequence[Tuple[str, bool]],
) -> GateResult:
    """Gate regression: seluruh suite test harus PASS.

    test_results: list (suite_name, passed_bool). Deterministik.
    """
    failed = [(name, ok) for name, ok in test_results if not ok]
    details = tuple("%s=%s" % (n, "PASS" if o else "FAIL") for n, o in test_results)
    return GateResult(
        name="regression",
        ok=not failed,
        details=details,
    )


# --- WP-31 Compliance gate ---------------------------------------------------

def compliance_gate() -> GateResult:
    """Gate compliance: seluruh group PEX/MEX/CX/EX harus PASS."""
    failures = _compliance_gates()
    return GateResult(
        name="compliance",
        ok=not failures,
        details=failures or ("PEX/MEX/CX/EX all pass",),
    )


# --- WP-32 Certification gate ------------------------------------------------

@dataclass(frozen=True)
class IntegrationCertification:
    """Hasil sertifikasi integrasi platform (engineering, read-only).

    Merangkum status seluruh gate; menandai platform integration READY
    (untuk ditinjau Architect) bila semua gate lulus.
    """

    regression: bool = False
    compliance: bool = False
    production_readiness: bool = False

    @property
    def certified(self) -> bool:
        return self.regression and self.compliance and self.production_readiness

    @property
    def summary(self) -> Tuple[str, ...]:
        return ("regression=%s" % ("PASS" if self.regression else "FAIL"),
                "compliance=%s" % ("PASS" if self.compliance else "FAIL"),
                "readiness=%s" % ("PASS" if self.production_readiness else "FAIL"))


def certification_gate(
    regression: bool, compliance: bool, readiness: bool
) -> IntegrationCertification:
    """Susun sertifikasi integrasi dari hasil gate (deterministik)."""
    return IntegrationCertification(
        regression=regression,
        compliance=compliance,
        production_readiness=readiness,
    )


# --- WP-33 Production readiness ---------------------------------------------

@dataclass(frozen=True)
class ReadinessAttributes:
    """Atribut kesiapan produksi platform (read-only)."""

    api_count: int = 0
    domain_count: int = 0
    perspective_count: int = 0
    bounded_context: str = "platform"
    presentation_passive: bool = True


def production_readiness_check(
    attributes: ReadinessAttributes,
) -> GateResult:
    """Gate produksi: platform harus punya struktur + pasif-saja.

    Menilai kesiapan berdasarkan atribut terukur (bukan tebakan).
    """
    issues = []
    if attributes.api_count <= 0:
        issues.append("tidak ada API")
    if attributes.domain_count <= 0:
        issues.append("tidak ada domain")
    if attributes.perspective_count <= 0:
        issues.append("tidak ada perspective")
    if not attributes.presentation_passive:
        issues.append("presentation bukan passive")
    return GateResult(
        name="production_readiness",
        ok=not issues,
        details=tuple(issues) or ("structurally ready & presentation-passive",),
    )
