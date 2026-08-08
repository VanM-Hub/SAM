"""Developer Experience - CLI onboarding logic (E2-G1).

Menyediakan logika murni (pure, testable tanpa CLI) untuk command onboarding
CLI:
- `doctor`: diagnosa kesehatan instalasi & environment (reuse DependencyChecker
  + EnvironmentValidator dari WP-E2.1, tanpa duplikasi).
- `version`: informasi versi package.
- `init`: rencana onboarding project (inspect kesiapan repo + dry-run
  bootstrap). Scaffold starter-project penuh adalah scope WP-E2.4 (E5-G1),
  bukan di sini.

Prinsip (EA-002):
- Modul `sam.devx` stand-alone; TIDAK mengubah runtime/governance/deployment/
  Foundation existing.
- Reuse komponen WP-E2.1 (checker/validator/bootstrap) - tidak duplikasi logika.
- Hanya menyusun/validasi; aksi aktual (apply) dilakukan via bootstrap apply=True.
- Purely stdlib untuk inti logika; CLI handler memakai Typer di lapisan CLI.
"""

from __future__ import annotations

import importlib.metadata as _md
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .dependencies import DependencyChecker
from .environment import EnvironmentValidator
from .installer import BootstrapInstaller, bootstrap
from .state import DependencyCheck, ComponentCheck


__all__ = [
    "DoctorReport",
    "InitPlan",
    "version_string",
    "doctor",
    "init_plan",
]


@dataclass
class DoctorReport:
    """Hasil diagnosa kesehatan instalasi & environment (E2-G1 doctor)."""

    version: str
    dependency_checks: List[DependencyCheck] = field(default_factory=list)
    environment_checks: List[ComponentCheck] = field(default_factory=list)
    all_ok: bool = True
    blocking_issues: List[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            "SAM Doctor v{4}: {0}\n"
            "  dependencies : {1}\n"
            "  environment  : {2}\n"
            "  issues       : {3}".format(
                "sehat" if self.all_ok else "ada masalah",
                len(self.dependency_checks),
                len(self.environment_checks),
                len(self.blocking_issues),
                self.version,
            )
        )


@dataclass
class InitPlan:
    """Rencana onboarding project (E2-G1 init, dry-run)."""

    project_root: str
    structure_ok: bool
    bootstrap_report_ok: bool
    phases: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return self.structure_ok and self.bootstrap_report_ok


def version_string() -> str:
    """Versi package SAM (prioritas metadata, fallback sam.__version__)."""
    try:
        from sam import __version__ as pkg  # type: ignore[import]

        return str(pkg)
    except Exception:  # noqa: BLE001
        try:
            return str(_md.version("sam"))  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            return "unknown"


def doctor(
    project_root: Optional[Path] = None,
) -> DoctorReport:
    """Diagnosa kesehatan instalasi & environment.

    Menggabungkan DependencyChecker (python/pip/setuptools/wheel/sam import)
    dan EnvironmentValidator (executable/venv/repo/PYTHONPATH/writable).
    Sama dengan fase awal bootstrap, tapi non-destruktif & read-only.
    """
    checker = DependencyChecker()
    env = EnvironmentValidator(project_root)

    dep_checks = checker.run(include_optional=True)
    env_checks = env.run()

    blocking: List[str] = []
    for c in dep_checks:
        if getattr(c, "is_blocking", False):
            blocking.append("dependency: {0}".format(c.name))
        elif getattr(c, "required", False) and not c.passed:
            blocking.append("dependency: {0}".format(c.name))
    for c in env_checks:
        if not c.passed:
            blocking.append("environment: {0}".format(c.component))

    return DoctorReport(
        version=version_string(),
        dependency_checks=dep_checks,
        environment_checks=env_checks,
        all_ok=not blocking,
        blocking_issues=blocking,
    )


def init_plan(
    project_root: Optional[Path] = None,
) -> InitPlan:
    """Rencana onboarding project (dry-run).

    - Cek struktur repo minimal (pyproject.toml + src/sam/__init__.py).
    - Jalankan `bootstrap(..., apply=False)` dry-run untuk validasi end-to-end.
    - Susun next-steps untuk early adopter.

    Tidak mengubah filesystem (dry-run). Scaffold full project adalah WP-E2.4.
    """
    env = EnvironmentValidator(project_root)
    structure_ok = env.check_repo_structure().passed

    report = bootstrap(project_root=env.project_root, apply=False)
    phases = [p.value for p in report.phases_run]

    next_steps: List[str] = []
    notes: List[str] = []
    if not structure_ok:
        notes.append("Struktur repo belum lengkap (butuh pyproject.toml + src/sam/__init__.py).")
        next_steps.append("Jalankan `sam init --scaffold` (tersedia di WP-E2.4) untuk starter project.")
    else:
        next_steps.append("Jalankan `sam init --apply` untuk membuat venv & install editable.")
    next_steps.append("Jalankan `sam doctor` untuk verifikasi kesehatan instalasi.")
    next_steps.append("Jalankan `sam version` untuk cek versi terpasang.")

    return InitPlan(
        project_root=str(env.project_root),
        structure_ok=structure_ok,
        bootstrap_report_ok=report.success,
        phases=phases,
        next_steps=next_steps,
        notes=notes,
    )
