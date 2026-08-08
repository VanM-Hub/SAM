"""Developer Experience - environment validation.

Memvalidasi lingkungan tempat SAM akan dijalankan/diinstal:
- Python executable tersedia & dapat dieksekusi.
- Virtual environment terdeteksi (atau dapat dibuat).
- Lokasi instalasi writable.
- PYTHONPATH/import path menunjuk ke `src/` bila diperlukan.
- Struktur repo (pyproject.toml, src/sam/__init__.py) hadir.

Purely stdlib; read-only (tidak membuat venv, hanya mendeteksi & melaporkan).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Set

from .state import (
    CheckSeverity,
    ComponentCheck,
    EnvStatus,
    MISSING_PYTHON_MIN,
)


__all__ = ["EnvironmentValidator"]


class EnvironmentValidator:
    """Memvalidasi environment SAM untuk instalasi dari source."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        # Jika tidak diberikan, cari dari lokasi modul ini (src/sam/devx).
        self.project_root = project_root or self._infer_project_root()

    @staticmethod
    def _infer_project_root() -> Path:
        here = Path(__file__).resolve()
        # .../src/sam/devx/environment.py -> naik ke root src, lalu project
        src_dir = here.parents[2]  # src/
        return src_dir.parent

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _in_venv() -> bool:
        prefix = getattr(sys, "prefix", "")
        base = getattr(sys, "base_prefix", "")
        # PyPy convention: base_prefix boleh sama.
        return prefix != base

    @staticmethod
    def _version_tolerance() -> bool:
        v = sys.version_info
        return (v.major, v.minor) >= MISSING_PYTHON_MIN

    def _is_writable(self, path: Path) -> bool:
        try:
            if path.is_dir():
                test = path / (".sam_devx_write_test")
            else:
                test = path.parent / (".sam_devx_write_test")
            test.write_text("", encoding="utf-8")
            test.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    # -- checks ----------------------------------------------------------
    def check_python_executable(self) -> ComponentCheck:
        exe = sys.executable
        if not exe:
            return ComponentCheck(
                "python_executable", EnvStatus.MISSING, "sys.executable kosong."
            )
        return ComponentCheck(
            "python_executable",
            EnvStatus.OK,
            "Python executable ditemukan.",
            detail=str(exe),
        )

    def check_python_version(self) -> ComponentCheck:
        v = sys.version_info
        if not self._version_tolerance():
            return ComponentCheck(
                "python_version",
                EnvStatus.WRONG_VERSION,
                "Python {0}.{1} di bawah minimum 3.8.".format(v.major, v.minor),
                detail="digunakan interpreter: {0}".format(sys.executable),
            )
        return ComponentCheck(
            "python_version",
            EnvStatus.OK,
            "Python {0}.{1} OK (>=3.8).".format(v.major, v.minor),
        )

    def check_virtualenv(self) -> ComponentCheck:
        if self._in_venv():
            return ComponentCheck(
                "virtualenv",
                EnvStatus.OK,
                "Virtual environment terdeteksi (direkomendasikan).",
                detail=getattr(sys, "prefix", ""),
            )
        return ComponentCheck(
            "virtualenv",
            EnvStatus.NOT_PRESENT,
            "Tidak dalam virtual environment. Disarankan: python -m venv .venv.",
        )

    def check_repo_structure(self) -> ComponentCheck:
        root = self.project_root
        pyproject = root / "pyproject.toml"
        src_init = root / "src" / "sam" / "__init__.py"
        if pyproject.is_file() and src_init.is_file():
            return ComponentCheck(
                "repo_structure",
                EnvStatus.OK,
                "Struktur repo lengkap (pyproject.toml + src/sam).",
                detail=str(root),
            )
        missing: List[str] = []
        if not pyproject.is_file():
            missing.append("pyproject.toml")
        if not src_init.is_file():
            missing.append("src/sam/__init__.py")
        return ComponentCheck(
            "repo_structure",
            EnvStatus.MISSING,
            "Struktur repo tidak lengkap: " + ", ".join(missing),
            detail=str(root),
        )

    def check_pythonpath(self) -> ComponentCheck:
        """Cek apakah src/ ada di sys.path (untuk penggunaan source)."""
        src_dir = self.project_root / "src"
        paths: Set[str] = {os.path.abspath(p) for p in sys.path if p}
        target = os.path.abspath(str(src_dir))
        if target in paths:
            return ComponentCheck(
                "pythonpath",
                EnvStatus.OK,
                "'{0}' ada di sys.path.".format(target),
            )
        if target in paths:
            return ComponentCheck("pythonpath", EnvStatus.OK, "src/ di sys.path.")
        return ComponentCheck(
            "pythonpath",
            EnvStatus.NOT_PRESENT,
            "src/ tidak ada di sys.path. Set PYTHONPATH=src atau jalankan instalasi editable.",
        )

    def check_install_location_writable(self) -> ComponentCheck:
        # Area umum instalasi: project root (untuk editable) dan site-packages.
        root = self.project_root
        if self._is_writable(root):
            return ComponentCheck(
                "install_location",
                EnvStatus.OK,
                "Lokasi project writable (editabel install dimungkinkan).",
                detail=str(root),
            )
        return ComponentCheck(
            "install_location",
            EnvStatus.NOT_WRITABLE,
            "Lokasi project tidak writable. Periksa izin direktori.",
            detail=str(root),
        )

    # -- aggregate ---------------------------------------------------------
    def run(self) -> List[ComponentCheck]:
        return [
            self.check_python_executable(),
            self.check_python_version(),
            self.check_virtualenv(),
            self.check_repo_structure(),
            self.check_pythonpath(),
            self.check_install_location_writable(),
        ]

    def has_blocking_failure(self, checks: Sequence[ComponentCheck]) -> bool:
        """Apakah ada komponen REQUIRED yang gagal (python version / repo)."""
        for c in checks:
            if c.component in ("python_version", "repo_structure", "python_executable"):
                if not c.passed:
                    return True
        return False
