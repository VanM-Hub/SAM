"""Developer Experience - bootstrap installer (orchestrator satu perintah).

Menggabungkan: dependency validation -> environment validation -> automatic
environment initialization -> installation -> installation verification ->
diagnostics, menjadi satu proses bootstrap yang deterministik.

Prinsip (EA-002):
- Satu entry point (`bootstrap()` / `BootstrapInstaller.run()`).
- Deterministik: langkah berurutan, berhenti pada blocking failure.
- Verify-after-install: verifikasi impor & entry point sebelum sukses.
- TIDAK mengubah runtime / governance / deployment / Foundation existing.
- Action aktual (venv create, pip install) dilakukan via subprocess hanya bila
  `apply=True`; mode `dry_run=True` (default untuk keamanan) hanya menyusun
  rencana & memvalidasi tanpa mengubah filesystem di luar tmpnya sendiri.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from .dependencies import DependencyChecker
from .environment import EnvironmentValidator
from .report import InstallationReportBuilder
from .state import (
    DependencyCheck,
    InstallPhase,
    InstallStepRecord,
    InstallationReport,
    ComponentCheck,
)
from .verifier import InstallationVerifier


__all__ = ["BootstrapInstaller", "bootstrap"]


class BootstrapInstaller:
    """Orchestrator proses bootstrap instalasi SAM (one-command)."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        apply: bool = False,
        venv_dir: Optional[str] = ".venv",
    ) -> None:
        self.project_root = project_root or EnvironmentValidator().project_root
        self.apply = apply
        self.venv_dir = venv_dir
        self._checker = DependencyChecker()
        self._env = EnvironmentValidator(self.project_root)
        self._verifier = InstallationVerifier(self.project_root)
        self._report_builder = InstallationReportBuilder()

    # -- plumbing ---------------------------------------------------------
    @staticmethod
    def _step(phase: InstallPhase, ok: bool, message: str, blocking: bool = False, detail: str = "") -> InstallStepRecord:
        return InstallStepRecord(phase=phase, ok=ok, message=message, blocking=blocking, detail=detail)

    def _venv_python(self) -> Path:
        if sys.platform.startswith("win"):
            return self.project_root / str(self.venv_dir) / "Scripts" / "python.exe"
        return self.project_root / str(self.venv_dir) / "bin" / "python"

    def _run_cmd(self, argv: Sequence[str]) -> Tuple[int, str]:
        try:
            proc = subprocess.run(
                list(argv),
                capture_output=True,
                text=True,
                timeout=600,
                env=os.environ.copy(),
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            return int(proc.returncode), out.strip()
        except Exception as exc:  # noqa: BLE001
            return -1, str(exc)

    # -- phases utama ------------------------------------------------------
    def phase_dependency_validation(self) -> List[InstallStepRecord]:
        checks = self._checker.run(include_optional=True)
        self._dep_checks = checks
        return [self._step(InstallPhase.DEPENDENCY_VALIDATION, True, "Dependency validation selesai.")]

    def phase_environment_validation(self) -> List[InstallStepRecord]:
        checks = self._env.run()
        self._env_checks = checks
        return [self._step(InstallPhase.ENVIRONMENT_VALIDATION, True, "Environment validation selesai.")]

    def phase_environment_init(self) -> List[InstallStepRecord]:
        """Inisialisasi environment otomatis (buat venv bila belum ada)."""
        venv_dir = self.project_root / str(self.venv_dir)
        steps: List[InstallStepRecord] = []
        if not self.apply:
            steps.append(
                self._step(
                    InstallPhase.ENVIRONMENT_INIT,
                    True,
                    "Dry-run: rencana buat virtual environment di '{0}'.".format(venv_dir),
                )
            )
            return steps
        if venv_dir.exists() and (venv_dir / "pyvenv.cfg").is_file():
            steps.append(
                self._step(InstallPhase.ENVIRONMENT_INIT, True, "Virtual environment sudah ada, dilewati.", detail=str(venv_dir))
            )
            return steps
        code, out = self._run_cmd([sys.executable, "-m", "venv", str(venv_dir)])
        if code != 0:
            steps.append(
                self._step(
                    InstallPhase.ENVIRONMENT_INIT,
                    False,
                    "Gagal membuat venv: " + out[:200],
                    blocking=True,
                )
            )
            return steps
        steps.append(
            self._step(InstallPhase.ENVIRONMENT_INIT, True, "Virtual environment dibuat.", detail=str(venv_dir))
        )
        return steps

    def phase_installation(self) -> List[InstallStepRecord]:
        steps: List[InstallStepRecord] = []
        if not self.apply:
            steps.append(
                self._step(
                    InstallPhase.INSTALLATION,
                    True,
                    "Dry-run: rencana 'pip install -e .' di project '{0}'.".format(self.project_root),
                )
            )
            return steps
        python = sys.executable
        if (self.project_root / str(self.venv_dir) / "pyvenv.cfg").is_file():
            python = str(self._venv_python())
        code, out = self._run_cmd([python, "-m", "pip", "install", "-e", str(self.project_root)])
        if code != 0:
            steps.append(
                self._step(
                    InstallPhase.INSTALLATION,
                    False,
                    "Instalasi editable gagal: " + out[:200],
                    blocking=True,
                )
            )
            return steps
        steps.append(
            self._step(InstallPhase.INSTALLATION, True, "Instalasi editable berhasil.")
        )
        return steps

    def phase_install_verification(self) -> List[InstallStepRecord]:
        """Verifikasi instalasi.

        Dalam dry-run (apply=False) TIDAK ada instalasi nyata yang terjadi,
        sehingga verifikasi import/entry-point/version ditunda (skipped) dan
        tidak bersifat blocking. Verifikasi aktual hanya bermakna setelah
        `apply=True` benar-benar meng-install SAM. Ini membuat dry-run
        deterministik di semua environment (tidak bergantung pada apakah
        'sam' kebetulan importable dari proses pytest saat itu).
        """
        steps: List[InstallStepRecord] = []
        if not self.apply:
            steps.append(
                self._step(
                    InstallPhase.INSTALL_VERIFICATION,
                    True,
                    "Dry-run: verifikasi instalasi ditunda (jalankan apply=True untuk memverifikasi).",
                )
            )
            return steps
        result = self._verifier.verify()
        for item in result.checks:
            steps.append(
                self._step(
                    InstallPhase.INSTALL_VERIFICATION,
                    item.ok,
                    item.message,
                    blocking=item.required and not item.ok,
                )
            )
        return steps

    def phase_diagnostics(self) -> List[InstallStepRecord]:
        steps: List[InstallStepRecord] = []
        diag = self._verifier.diagnostics()
        has_warning = False
        for key, lines in diag.items():
            if lines:
                has_warning = True
        steps.append(
            self._step(
                InstallPhase.DIAGNOSTICS,
                True,
                "Diagnostics dikumpulkan" + (" (ada catatan)." if has_warning else " (bersih)."),
            )
        )
        return steps

    # -- orchestrator -------------------------------------------------------
    def run(self) -> InstallationReport:
        """Jalankan seluruh fase bootstrap. Kembalikan laporan akhir."""
        report = InstallationReport()

        phase_handlers = [
            (InstallPhase.DEPENDENCY_VALIDATION, self.phase_dependency_validation),
            (InstallPhase.ENVIRONMENT_VALIDATION, self.phase_environment_validation),
            (InstallPhase.ENVIRONMENT_INIT, self.phase_environment_init),
            (InstallPhase.INSTALLATION, self.phase_installation),
            (InstallPhase.INSTALL_VERIFICATION, self.phase_install_verification),
            (InstallPhase.DIAGNOSTICS, self.phase_diagnostics),
        ]

        for phase, handler in phase_handlers:
            steps = handler()
            report.phases_run.append(phase)
            report.steps.extend(steps)
            if any(s.blocking and not s.ok for s in steps):
                break

        # Kumpulkan hasil checker/verifier ke laporan
        report.dependency_checks = list(getattr(self, "_dep_checks", []))
        report.component_checks = list(getattr(self, "_env_checks", []))
        report.diagnostics = self._verifier.diagnostics()

        # Tentukan sukses: semua langkah OK & tidak ada blocking fail.
        failed = [s for s in report.steps if not s.ok and s.blocking]
        report.success = not failed

        self._report_builder.build_summary(report)
        return report


def bootstrap(
    project_root: Optional[Path] = None,
    apply: bool = False,
    venv_dir: str = ".venv",
) -> InstallationReport:
    """Fungsi satu-perintah untuk menjalankan bootstrap instalasi SAM."""
    installer = BootstrapInstaller(
        project_root=project_root,
        apply=apply,
        venv_dir=venv_dir,
    )
    return installer.run()
