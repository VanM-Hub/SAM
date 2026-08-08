"""Developer Experience - Starter project scaffold (E5-G1, WP-E2.4).

Menyediakan logika murni (pure, testable tanpa CLI) untuk membuat struktur
project SAM baru yang lengkap: Mission + Workflow + Runtime minimum +
pyproject + package. Menutup gap E5-G1 (High): tidak ada starter project /
template repository untuk project SAM baru.

Prinsip (EA-002):
- Modul `sam.devx` stand-alone; TIDAK mengubah runtime/governance/deployment/
  Foundation existing.
- `scaffold_project(...)` default dry-run (apply=False): TIDAK menulis apa pun
  ke disk; hanya menghitung file yang akan dibuat + validasi + laporan.
- `apply=True`: menulis file ke target dir dengan aman (tidak menimpa file
  yang sudah ada). Idempotent.
- Purely stdlib; CLI handler memakai Typer di lapisan CLI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


__all__ = [
    "ScaffoldProject",
    "DEFAULT_SCAFFOLD_FILES",
    "build_files",
    "scaffold_project",
]


# --- Template helpers -----------------------------------------------------


def _pyproject(name: str, version: str) -> str:
    return (
        "[build-system]\n"
        "requires = [\"setuptools>=68\"]\n"
        "build-backend = \"setuptools.build_meta\"\n"
        "\n"
        "[project]\n"
        'name = "{0}"\n'
        'version = "{1}"\n'
        'description = "SAM project: {0}"\n'
        'requires-python = ">=3.8"\n'
        "dependencies = [\n"
        '    "sam-ops>=1.0.0",\n'
        "]\n"
        "\n"
        "[tool.setuptools.packages.find]\n"
        'where = ["src"]\n'
    ).format(name, version)


def _package_init(name: str) -> str:
    return (
        '"""Package untuk project SAM {0}."""\n'
        "\n"
        "__version__ = \"0.1.0\"\n"
    ).format(name)


def _mission_yaml(name: str) -> str:
    return (
        "name: {0}-mission\n"
        "description: Mission utama project {0}\n"
        "version: \"0.1.0\"\n"
        "objectives:\n"
        "  - id: first-objective\n"
        "    description: Capaian pertama yang harus dicapai.\n"
    ).format(name)


def _workflow_yaml(name: str) -> str:
    return (
        "name: hello-{0}\n"
        "description: Workflow contoh untuk project {0}\n"
        "steps:\n"
        "  - id: start\n"
        "    capability: sam.log\n"
        "    inputs:\n"
        "      message: \"SAM starter project berjalan\"\n"
        "    transition:\n"
        "      on_success: done\n"
        "  - id: done\n"
        "    capability: sam.log\n"
    ).format(name)


def _subpackage_init(name: str, sub: str) -> str:
    return '"""Package {0} ({1}) untuk project {2}."""\n'.format(sub, sub, name)


# --- File manifest --------------------------------------------------------


def build_files(name: str, version: str) -> Dict[str, str]:
    """Membangun mapping path-relatif -> konten untuk scaffold project.

    Semua path relatif ke root project.
    """
    pkg = name.replace("-", "_")
    return {
        "pyproject.toml": _pyproject(name, version),
        "README.md": "# {0}\n\nStarter project SAM (E5-G1). Menutup gap E5-G1: "
        "struktur project SAM baru (Mission + Workflow + Runtime).\n".format(name),
        "mission.yaml": _mission_yaml(name),
        "workflow.yaml": _workflow_yaml(name),
        "src/{0}/__init__.py".format(pkg): _package_init(name),
        "src/{0}/runtime/__init__.py".format(pkg): _subpackage_init(name, "runtime"),
        "src/{0}/mission/__init__.py".format(pkg): _subpackage_init(name, "mission"),
        "src/{0}/workflow/__init__.py".format(pkg): _subpackage_init(name, "workflow"),
    }


DEFAULT_SCAFFOLD_FILES: List[str] = [
    "pyproject.toml",
    "README.md",
    "mission.yaml",
    "workflow.yaml",
]


@dataclass
class ScaffoldProject:
    """Hasil scaffold starter project (E5-G1)."""

    name: str
    target_dir: str
    created: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    dry_run: bool = True
    validated: bool = False

    @property
    def ok(self) -> bool:
        return self.validated


def _validate_name(name: str) -> None:
    if not name or not name.strip():
        raise ValueError("Nama project tidak boleh kosong.")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_.")
    for ch in name.lower():
        if ch not in allowed:
            raise ValueError(
                "Nama project hanya boleh huruf kecil, angka, '-', '_', '.': {0!r}".format(name)
            )


def _validate_target(target: Path) -> None:
    if target.exists() and not target.is_dir():
        raise ValueError("Target scaffold harus berupa direktori: {0}".format(target))


def scaffold_project(
    name: str,
    target_dir: Optional[Path] = None,
    *,
    apply: bool = False,
    version: str = "0.1.0",
) -> ScaffoldProject:
    """Membuat starter project SAM baru.

    - `name`: nama project (digunakan untuk package, mission, workflow).
    - `target_dir`: direktori tujuan (default: ./<name> di cwd).
    - `apply=False` (default): dry-run - hanya menghitung & validasi, TIDAK
      menulis apa pun ke disk.
    - `apply=True`: menulis file scaffold (tidak menimpa yang sudah ada).
    """
    _validate_name(name)
    target: Path = Path(target_dir) if target_dir is not None else Path(name)
    _validate_target(target)

    files = build_files(name, version)

    # Validasi struktural (independen dari apply)
    keys = set(files)
    has_root = {"pyproject.toml", "README.md"}.issubset(keys)
    has_mission = "mission.yaml" in keys
    has_workflow = "workflow.yaml" in keys
    has_package = any(k.startswith("src/") and k.endswith("__init__.py") for k in keys)
    validated = has_root and has_mission and has_workflow and has_package

    created: List[str] = []
    skipped: List[str] = []

    if apply:
        for rel, content in files.items():
            dest = target / rel
            if dest.exists():
                skipped.append(rel)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            created.append(rel)
    else:
        # dry-run: tidak menulis; daftarkan semua file sebagai "akan dibuat"
        created = list(files.keys())

    return ScaffoldProject(
        name=name,
        target_dir=str(target),
        created=created,
        skipped=skipped,
        dry_run=not apply,
        validated=validated,
    )
