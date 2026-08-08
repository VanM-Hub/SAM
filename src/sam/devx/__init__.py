"""SAM Developer Experience - bootstrap installer & diagnostics.

Menutup gap E1-G1 (Priority WP-E2.1, Program E / MISSION-2E, EA-002):
"Tidak ada bootstrap installer otomatis - pengguna menyiapkan SAM secara manual."

Capability ini menyediakan one-command installation bootstrap:
- Dependency validation (python, pip, setuptools/wheel, sam import).
- Environment validation (executable, venv, repo structure, PYTHONPATH, writable).
- Automatic environment initialization (venv create, pip install -e .) - opsional.
- Installation verification (import, version, entry points, first-run API).
- Installation report (text & dict).
- Installation diagnostics (env + entry points + module version).

Boundary (EA-002):
- Berlaku hanya pada Developer Experience layer. TIDAK mengubah runtime,
  governance, deployment architecture, Foundation, launcher, atau Accepted ADR.
- Purely stdlib - tanpa dependency eksternal baru.
- Mode `apply=False` (dry-run default) tidak mengubah filesystem; mode
  `apply=True` baru mengeksekusi venv/pip install.
"""

from __future__ import annotations

from sam.devx.state import (
    MISSING_PYTHON_MIN,
    CheckSeverity,
    CheckStatus,
    ComponentCheck,
    DependencyCheck,
    DependencyStatus,
    EnvStatus,
    InstallPhase,
    InstallStepRecord,
    InstallationReport,
)
from sam.devx.dependencies import DependencyChecker
from sam.devx.environment import EnvironmentValidator
from sam.devx.installer import BootstrapInstaller, bootstrap
from sam.devx.report import InstallationReportBuilder
from sam.devx.verifier import (
    InstallationVerifier,
    VerificationResult,
    VerifyCheck,
)

__all__ = [
    "bootstrap",
    "BootstrapInstaller",
    "DependencyChecker",
    "EnvironmentValidator",
    "InstallationReportBuilder",
    "InstallationVerifier",
    "VerificationResult",
    "VerifyCheck",
    "ComponentCheck",
    "DependencyCheck",
    "DependencyStatus",
    "EnvStatus",
    "InstallPhase",
    "InstallStepRecord",
    "InstallationReport",
    "CheckSeverity",
    "CheckStatus",
    "MISSING_PYTHON_MIN",
]
