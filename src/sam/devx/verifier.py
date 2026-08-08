"""Developer Experience - installation verifier & diagnostics.

Memverifikasi bahwa instalasi SAM benar-benar berfungsi setelah proses
bootstrap:
- Package 'sam' dapat diimpor.
- Entry point CLI (sam) tersedia (jika terinstall).
- Versi package terbaca.
- First-run check: fungsi 'sam.observe'/'SAM' dapat diakses.

Purely stdlib; read-only (tidak mengubah filesystem).
"""

from __future__ import annotations

import importlib
import importlib.metadata as _md
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


__all__ = ["VerifyCheck", "VerificationResult", "InstallationVerifier"]


@dataclass(frozen=True)
class VerifyCheck:
    """Satu hasil verifikasi instalasi. Immutable (ADR-023)."""

    name: str
    ok: bool
    message: str
    required: bool = True


@dataclass
class VerificationResult:
    """Agregat hasil verifikasi. Dibangun incremental."""

    checks: List[VerifyCheck] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return all(c.ok for c in self.checks if c.required)


class InstallationVerifier:
    """Memverifikasi instalasi SAM berfungsi (importable + entry point)."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _import_sam() -> object:
        return importlib.import_module("sam")

    @staticmethod
    def _package_version() -> str:
        try:
            return _md.version("sam")  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            return ""

    @staticmethod
    def _entry_points() -> List[str]:
        try:
            eps = _md.entry_points()  # type: ignore[attr-defined]
            names: List[str] = []
            try:
                group = eps.select(group="console_scripts")  # type: ignore[attr-defined]
                names = [ep.name for ep in group]
            except AttributeError:
                group = eps.get("console_scripts", [])  # type: ignore[attr-defined]
                names = [ep.name for ep in group]
            return sorted(names)
        except Exception:  # noqa: BLE001
            return []

    # -- checks ----------------------------------------------------------
    def check_import(self) -> VerifyCheck:
        try:
            self._import_sam()
            return VerifyCheck("import_sam", True, "Package 'sam' berhasil diimpor.")
        except Exception as exc:  # noqa: BLE001
            return VerifyCheck("import_sam", False, "Gagal impor 'sam': {0}".format(exc)[:200])

    def check_version(self) -> VerifyCheck:
        ver = self._package_version()
        if not ver:
            return VerifyCheck(
                "package_version",
                False,
                "Versi package 'sam' tidak terbaca (belum terinstall / tidak editable).",
            )
        return VerifyCheck("package_version", True, "Versi package sam: {0}.".format(ver))

    def check_entry_points(self) -> VerifyCheck:
        eps = self._entry_points()
        cli = [e for e in eps if e in ("sam", "sam-console", "sam-desktop", "sam-headless", "sam-diagnostic")]
        if cli:
            return VerifyCheck(
                "entry_points",
                True,
                "Entry point CLI tersedia: {0}.".format(", ".join(cli)),
            )
        return VerifyCheck(
            "entry_points",
            False,
            "Entry point CLI sam belum terdaftar (pip install -e . belum dijalankan).",
        )

    def check_first_run(self) -> VerifyCheck:
        """First-run: pastikan object 'SAM' dapat diakses dari import sam."""
        try:
            sam = self._import_sam()
            has_sam = hasattr(sam, "SAM") or hasattr(sam, "observe")
            return VerifyCheck(
                "first_run_api",
                True if has_sam else False,
                "Public API 'SAM'/'observe' tersedia." if has_sam else "Public API 'SAM' belum diekspor.",
            )
        except Exception as exc:  # noqa: BLE001
            return VerifyCheck("first_run_api", False, "Gagal first-run check: {0}".format(exc)[:200])

    # -- aggregate ---------------------------------------------------------
    def verify(self) -> VerificationResult:
        res = VerificationResult()
        res.checks.extend(
            [
                self.check_import(),
                self.check_version(),
                self.check_entry_points(),
                self.check_first_run(),
            ]
        )
        return res

    def diagnostics(self) -> Dict[str, List[str]]:
        """Kumpulkan diagnostik env untuk laporan (non-blocking)."""
        diag: Dict[str, List[str]] = {}
        diag["python"] = ["{0} {1} ({2})".format(sys.executable, sys.version.split()[0], sys.platform)]
        diag["sam"] = ["version={0}".format(self._package_version() or "n/a")]
        eps = self._entry_points()
        diag["entry_points"] = eps if eps else ["(tidak ada entry point terdaftar)"]
        try:
            sam = self._import_sam()
            ver = getattr(sam, "__version__", "n/a")
            diag["sam_module"].append("__version__={0}".format(ver))
        except Exception:  # noqa: BLE001
            diag["sam_module"] = ["(import gagal)"]
        if "sam_module" not in diag:
            diag["sam_module"] = []
        return diag
