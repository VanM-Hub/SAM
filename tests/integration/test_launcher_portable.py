"""
H1 — Portable Deployment Evidence Tests.

Memverifikasi bahwa launcher .bat di root repo bersifat PORTABLE:
- Tidak ada path absolut/hardcoded (mengandung drive / absolute root).
- Menggunakan %~dp0 (path di-resolve dari lokasi script).
- Menggunakan PYTHONPATH relatif (%CD%\\src).
- Entry point Python masih memanggil jalur resmi sam.launcher.cli_entry.

Program D (MISSION-2D) — EA-002 Production Readiness Implementation,
WP-D2.1 (Priority P1, Gap H1 Portable Deployment).
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Launcher .bat yang wajib portable
LAUNCHER_BATS = [
    "SAM_CLI.bat",
    "SAM_Desktop.bat",
    "SAM_Ops.bat",
    "SAM_Run.bat",
    "SAM_Web.bat",
]

# Pola path absolut Windows (drive letter) atau root Unix
_ABSOLUTE_PATH_RE = re.compile(
    r"""
    (?P<drive>[A-Za-z]:[\\/]| / )      # C:\  atau  /... 
    """,
    re.VERBOSE,
)

# Pola hardcoded project path specifik (jika direlokasi, pasti salah)
_HARDCODED_PROJECT_RE = re.compile(
    r"[A-Za-z]:[\\/]+[^\"']*(?:src|\\src|/src)",
    re.IGNORECASE,
)


def _read_bat(name: str) -> str:
    path = REPO_ROOT / name
    assert path.exists(), f"Launcher tidak ditemukan: {name}"
    return path.read_text(encoding="utf-8")


class TestPortableLauncher:
    """Semua launcher .bat root harus portable (H1)."""

    @staticmethod
    def _check(name: str):
        content = _read_bat(name)
        return content

    def test_all_launcher_bats_exist(self):
        for name in LAUNCHER_BATS:
            assert (REPO_ROOT / name).exists(), f"Missing: {name}"

    def test_no_absolute_drive_path_in_bat(self):
        """Tidak boleh ada drive letter C:/D:/ dll sebagai path dasar."""
        for name in LAUNCHER_BATS:
            content = self._check(name)
            # cari absolute Windows drive path di baris perintah non-komentar
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("rem") or line.startswith("@echo") \
                        or line.startswith("echo"):
                    continue
                assert not re.search(r"[A-Za-z]:[\\/]", line), (
                    f"{name}: absolute drive path ditemukan -> {line}"
                )
                assert not line.startswith("/"), (
                    f"{name}: absolute root path ditemukan -> {line}"
                )

    def test_no_hardcoded_project_src_path(self):
        """Tidak boleh ada path <drive>\\...\\src hardcoded."""
        for name in LAUNCHER_BATS:
            content = self._check(name)
            assert not re.search(r"[A-Za-z]:[\\/]+[^\"']*src", content), (
                f"{name}: hardcoded project src path ditemukan"
            )

    def test_uses_relative_script_dir(self):
        """Harus pakai %~dp0 untuk resolve lokasi script (portable)."""
        for name in LAUNCHER_BATS:
            content = self._check(name)
            assert "%~dp0" in content, f"{name}: tidak memakai %~dp0"

    def test_uses_cd_to_relative_dir(self):
        """Harus cd ke direktori script secara relatif."""
        for name in LAUNCHER_BATS:
            content = self._check(name)
            assert re.search(r'cd\s*/d\s+"?%~dp0', content, re.IGNORECASE), (
                f"{name}: tidak cd /d ke %~dp0"
            )

    def test_uses_relative_pythonpath(self):
        """PYTHONPATH harus relatif terhadap CD (portable), bukan absolut."""
        for name in LAUNCHER_BATS:
            content = self._check(name)
            assert re.search(r"PYTHONPATH=%CD%", content, re.IGNORECASE), (
                f"{name}: PYTHONPATH tidak memakai %CD% (portable)"
            )

    def test_python_entry_point_intact(self):
        """Entry point Python tetap memanggil jalur resmi sam.launcher.cli_entry.
        SAM_Web.bat memakai jalur berbeda (sam.web.server via uvicorn) — sesuai desain.
        """
        for name in LAUNCHER_BATS:
            content = self._check(name)
            if name == "SAM_Web.bat":
                assert "sam.web.server" in content
                assert "uvicorn" in content
            else:
                assert "sam.launcher.cli_entry" in content, (
                    f"{name}: entry point sam.launcher.cli_entry hilang"
                )

    def test_python_executable_resolution(self):
        """Python dijalankan relatif dari .venv lokal (portable)."""
        for name in LAUNCHER_BATS:
            content = self._check(name)
            assert ".venv\\Scripts\\python.exe" in content or ".venv/Scripts/python.exe" in content, (
                f"{name}: python .venv relatif tidak ditemukan"
            )
