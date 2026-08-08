"""Developer Experience - state & DTOs.

Menutup gap E1-G1 (Priority WP-E2.1, Program E / MISSION-2E, EA-002):
"Tidak ada bootstrap installer otomatis - pengguna menyiapkan SAM secara manual
(venv + pip + PYTHONPATH)."

Design (konservatif terhadap constraint EA-002):
- Modul `sam.devx` berdiri sendiri (stand-alone) sebagai capability Developer
  Experience. TIDAK mengubah runtime, governance, deployment architecture,
  Foundation, atau launcher existing.
- Seluruh payload memakai Immutable DTO (ADR-023).
- Purely stdlib - tanpa dependency eksternal.

Scope: bootstrap installer, dependency validation, environment validation,
automatic environment initialization, installation verification, installation
diagnostics.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence


__all__ = [
    "CheckStatus",
    "CheckSeverity",
    "DependencyStatus",
    "EnvStatus",
    "ComponentCheck",
    "DependencyCheck",
    "InstallPhase",
    "InstallStepRecord",
    "InstallationReport",
    "MISSING_PYTHON_MIN",
]


# Python minimum yang didukung repo (selaras pyproject requires-python).
MISSING_PYTHON_MIN = (3, 8)


class CheckStatus(str, enum.Enum):
    """Status hasil pemeriksaan (dependency / environment / install)."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class CheckSeverity(str, enum.Enum):
    """Severity sebuah pemeriksaan jika gagal.

    - REQUIRED: gagal -> bootstrap berhenti (blocking).
    - RECOMMENDED: gagal -> warning, lanjut.
    - OPTIONAL: gagal -> catat, tidak menghalangi.
    """

    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class DependencyStatus(str, enum.Enum):
    """Status dependency yang diperiksa."""

    INSTALLED = "installed"
    MISSING = "missing"
    WRONG_VERSION = "wrong_version"
    NOT_REQUIRED = "not_required"


class EnvStatus(str, enum.Enum):
    """Status komponen environment."""

    OK = "ok"
    MISSING = "missing"
    WRONG_VERSION = "wrong_version"
    NOT_WRITABLE = "not_writable"
    NOT_PRESENT = "not_present"


@dataclass(frozen=True)
class DependencyCheck:
    """Hasil pemeriksaan satu dependency. Immutable (ADR-023)."""

    name: str
    required: bool
    severity: CheckSeverity
    status: DependencyStatus
    found_version: Optional[str] = None
    required_version: Optional[str] = None
    message: str = ""

    @property
    def passed(self) -> bool:
        """Lulus bila INSTALLED, atau tidak diwajibkan (NOT_REQUIRED)."""
        if not self.required:
            return True
        return self.status is DependencyStatus.INSTALLED

    @property
    def is_blocking(self) -> bool:
        """Blocking bila FAIL pada severity REQUIRED."""
        return (self.severity is CheckSeverity.REQUIRED) and (not self.passed)


@dataclass(frozen=True)
class ComponentCheck:
    """Hasil pemeriksaan satu komponen environment. Immutable (ADR-023)."""

    component: str
    status: EnvStatus
    message: str = ""
    detail: str = ""

    @property
    def passed(self) -> bool:
        return self.status is EnvStatus.OK


class InstallPhase(str, enum.Enum):
    """Fase-fase dalam proses bootstrap instalasi."""

    DEPENDENCY_VALIDATION = "dependency_validation"
    ENVIRONMENT_VALIDATION = "environment_validation"
    ENVIRONMENT_INIT = "environment_init"
    INSTALLATION = "installation"
    INSTALL_VERIFICATION = "install_verification"
    DIAGNOSTICS = "diagnostics"


@dataclass(frozen=True)
class InstallStepRecord:
    """Rekaman satu langkah instalasi. Immutable (ADR-023)."""

    phase: InstallPhase
    ok: bool
    message: str = ""
    blocking: bool = False
    detail: str = ""


@dataclass
class InstallationReport:
    """Laporan instalasi lengkap. Hasil akhir bootstrap.

    Tidak frozen karena disusun incremental oleh builder (bukan payload
    immutable - melainkan agregat laporan). Data bertipe immutable atau
    primitive.
    """

    success: bool = False
    phases_run: List[InstallPhase] = field(default_factory=list)
    dependency_checks: List[DependencyCheck] = field(default_factory=list)
    component_checks: List[ComponentCheck] = field(default_factory=list)
    steps: List[InstallStepRecord] = field(default_factory=list)
    summary: Dict[str, str] = field(default_factory=dict)
    diagnostics: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def blocking_dependencies_failed(self) -> List[DependencyCheck]:
        return [d for d in self.dependency_checks if d.is_blocking]

    @property
    def component_failures(self) -> List[ComponentCheck]:
        return [c for c in self.component_checks if not c.passed]

    @property
    def warnings(self) -> int:
        return len(self.steps) - self.ok_steps

    @property
    def ok_steps(self) -> int:
        return sum(1 for s in self.steps if s.ok)

    @property
    def failed_steps(self) -> List[InstallStepRecord]:
        return [s for s in self.steps if not s.ok]
