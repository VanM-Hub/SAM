"""Developer Experience - dependency validation.

Memeriksa dependency yang dibutuhkan untuk menjalankan SAM dari source:
- Python version (>= MISSING_PYTHON_MIN).
- Package manager (pip) tersedia.
- Build backend (setuptools/wheel) tersedia untuk instalasi editable.
- Package `sam` sudah terinstall (editable) atau modul dapat diimpor.

Purely stdlib; tidak mengeksekusi instalasi - hanya memvalidasi (detection).
"""

from __future__ import annotations

import importlib
import importlib.metadata as _md
import platform
import sys
from typing import Dict, List, Optional, Sequence, Tuple

from .state import (
    MISSING_PYTHON_MIN,
    CheckSeverity,
    CheckStatus,
    DependencyCheck,
    DependencyStatus,
)


__all__ = ["DependencyChecker"]


_VERSION_TUPLES: Dict[str, Tuple[int, ...]] = {}


def _parse_version(text: Optional[str]) -> Optional[Tuple[int, ...]]:
    """Parse string versi menjadi tuple angka. Robust terhadap label."""

    if not text:
        return None
    parts: List[int] = []
    for chunk in text.replace("-", ".").split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        if digits:
            parts.append(int(digits))
        if len(parts) == 3:
            break
    return tuple(parts[:3]) if parts else None


class DependencyChecker:
    """Memvalidasi dependency environment untuk instalasi SAM.

    Deteksi only: membaca interpreter tersedia, importlib.metadata, dan
    importlib.util. Tidak menulis apa pun ke environment.
    """

    def __init__(self, python_min: Tuple[int, ...] = MISSING_PYTHON_MIN) -> None:
        self.python_min = python_min
        self._sys: object = sys

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _python_version() -> Tuple[int, ...]:
        return (sys.version_info.major, sys.version_info.minor)

    @staticmethod
    def _has_module(module: str) -> bool:
        try:
            importlib.util.find_spec(module)  # type: ignore[attr-defined]
            return True
        except (ImportError, AttributeError, ValueError):
            return False

    @staticmethod
    def _package_version(dist_name: str) -> Optional[str]:
        try:
            return _md.version(dist_name)  # type: ignore[attr-defined]
        except (_md.PackageNotFoundError, Exception):  # type: ignore[attr-defined]
            return None

    # -- checks ----------------------------------------------------------
    def check_python(self) -> DependencyCheck:
        actual = self._python_version()
        name = "python"
        req_str = ".".join(str(x) for x in self.python_min)
        ver_str = ".".join(str(x) for x in actual)
        if actual < self.python_min:
            return DependencyCheck(
                name=name,
                required=True,
                severity=CheckSeverity.REQUIRED,
                status=DependencyStatus.WRONG_VERSION,
                found_version=ver_str,
                required_version=">=" + req_str,
                message="Python {0} terdeteksi, minimum {1}.".format(ver_str, req_str),
            )
        return DependencyCheck(
            name=name,
            required=True,
            severity=CheckSeverity.REQUIRED,
            status=DependencyStatus.INSTALLED,
            found_version=ver_str,
            required_version=">=" + req_str,
            message="Python {0} OK (minimum {1}).".format(ver_str, req_str),
        )

    def check_pip(self) -> DependencyCheck:
        name = "pip"
        if self._has_module("pip"):
            packages = self._list_packages()
            ver = packages.get("pip")
            return DependencyCheck(
                name=name,
                required=True,
                severity=CheckSeverity.REQUIRED,
                status=DependencyStatus.INSTALLED,
                found_version=ver or "unknown",
                message="pip tersedia ({}).".format(ver or "version unknown"),
            )
        return DependencyCheck(
            name=name,
            required=True,
            severity=CheckSeverity.REQUIRED,
            status=DependencyStatus.MISSING,
            message="pip tidak ditemukan. Install pip terlebih dahulu.",
        )

    def check_build_backend(self) -> DependencyCheck:
        """Cek setuptools & wheel (build backend pyproject)."""
        found: List[str] = []
        for pkg in ("setuptools", "wheel"):
            ver = self._package_version(pkg)
            if ver:
                found.append("{}={}".format(pkg, ver))
        if len(found) == 2:
            return DependencyCheck(
                name="build-backend",
                required=True,
                severity=CheckSeverity.REQUIRED,
                status=DependencyStatus.INSTALLED,
                found_version="; ".join(found),
                message="Build backend tersedia (setuptools + wheel).",
            )
        return DependencyCheck(
            name="build-backend",
            required=True,
            severity=CheckSeverity.REQUIRED,
            status=DependencyStatus.MISSING,
            found_version="; ".join(found) or None,
            message="setuptools/wheel belum lengkap. Jalankan: pip install 'setuptools>=64' wheel.",
        )

    def check_sam_importable(self) -> DependencyCheck:
        name = "sam"
        if self._has_module("sam"):
            return DependencyCheck(
                name=name,
                required=True,
                severity=CheckSeverity.REQUIRED,
                status=DependencyStatus.INSTALLED,
                message="Package 'sam' dapat diimpor dari environment ini.",
            )
        return DependencyCheck(
            name=name,
            required=True,
            severity=CheckSeverity.REQUIRED,
            status=DependencyStatus.MISSING,
            message=(
                "Package 'sam' tidak dapat diimpor. Jalankan instalasi editable: "
                "pip install -e . (atau pastikan PYTHONPATH menunjuk ke src/)."
            ),
        )

    def check_optional(self) -> List[DependencyCheck]:
        """Check optional (RECOMMENDED) — turntable optional dependency."""
        checks: List[DependencyCheck] = []

        # tkinter (desktop optional)
        has_tk = self._has_module("tkinter")
        checks.append(
            DependencyCheck(
                name="tkinter",
                required=False,
                severity=CheckSeverity.RECOMMENDED,
                status=DependencyStatus.INSTALLED if has_tk else DependencyStatus.NOT_REQUIRED,
                message=(
                    "tkinter tersedia (opsional untuk desktop)."
                    if has_tk
                    else "tkinter tidak terdeteksi (opsional, hanya untuk desktop app)."
                ),
            )
        )
        return checks

    @staticmethod
    def _list_packages() -> Dict[str, str]:
        out: Dict[str, str] = {}
        try:
            for d in _md.distributions():  # type: ignore[attr-defined]
                name = (d.metadata.get("Name") or "").lower()
                ver = (d.version or "")
                if name:
                    out.setdefault(name, ver)
        except Exception:
            pass
        return out

    # -- aggregate ---------------------------------------------------------
    def run(self, include_optional: bool = True) -> List[DependencyCheck]:
        """Jalankan semua pemeriksaan dependency. Kembalikan daftar hasil."""
        checks: List[DependencyCheck] = [
            self.check_python(),
            self.check_pip(),
            self.check_build_backend(),
            self.check_sam_importable(),
        ]
        if include_optional:
            checks.extend(self.check_optional())
        return checks

    def summary(self, checks: Sequence[DependencyCheck]) -> Dict[str, int]:
        counts: Dict[str, int] = {"pass": 0, "warn": 0, "fail": 0, "blocking": 0}
        for c in checks:
            if c.is_blocking:
                counts["blocking"] += 1
            if c.passed:
                counts["pass"] += 1
            elif c.required:
                counts["fail"] += 1
            else:
                counts["warn"] += 1
        return counts
