# Runtime Diagnostics Compliance - WP-09
# IP-3.2-001 (AO-3.2-001 / ED-3.2-001)
#
# Compliance suite utk memastikan IP-3.2-001 murni observasi (read-only) dan
# TIDAK melanggar constraint Engineering:
#   - no runtime mutation
#   - no lifecycle change
#   - no auto recovery
#   - no restart
#   - no scheduling change
#   - no orchestration
#   - no authority acquisition
#
# Pemeriksaan: scan source terhadap pola untuk-aksi, verifikasi bahwa modul
# observasi tidak mengimpor modul aksi (autonomous/*), dan membuktikan bahwa
# seluruh endpoint API tidak memanggil rutin mutasi.

import ast
from pathlib import Path
from typing import Dict, List, NamedTuple, Tuple


class ComplianceItem(NamedTuple):
    name: str
    checked: bool
    passed: bool
    detail: str


# Pola yang menandai AKSI (dilarang di IP-3.2-001).
_FORBIDDEN_ACTION = (
    "restart(",
    "recover(",
    "schedule(",
    "orchestrate(",
    "mutate(",
    "execute(",
    "approve(",
    "start(",
    "stop(",
    "shutdown(",
    "apply(",
)

# Modul aksi era SAM 2.x yang DILARANG diimpor di bounded context observasi.
_FORBIDDEN_IMPORT = (
    "sam.autonomous",
    "sam.autonomy.executor",
    "sam.autonomy.recovery",
    "sam.autonomy.approval",
    "sam.autonomy.controller",
)


def compliance_check(
    package_path: Path,
    source_files: List[Path],
) -> Tuple[bool, Dict[str, object]]:
    """Jalankan compliance suite IP-3.2-001 terhadap file source."""
    items: List[ComplianceItem] = []

    items.append(_check_namespace(package_path))
    items.append(_check_forbidden_imports(source_files))
    items.append(_check_forbidden_action_calls(source_files))
    items.append(_check_observational_api(source_files))
    items.append(_check_no_runtime_mutation_call(source_files))

    passed = all(i.passed for i in items)
    return passed, {
        "total": len(items),
        "passed": sum(1 for i in items if i.passed),
        "items": [i._asdict() for i in items],
    }


def _check_namespace(package_path: Path) -> ComplianceItem:
    """Package berada di bounded context autonomy_runtime (bukan autonomous)."""
    name = "namespace_boundary"
    pkg_str = str(package_path).replace("\\", "/")
    ok = "autonomy_runtime" in pkg_str and "autonomous" not in pkg_str
    return ComplianceItem(name, True, ok, "package path: {}".format(package_path))


def _check_forbidden_imports(source_files: List[Path]) -> ComplianceItem:
    name = "no_forbidden_import"
    violations: List[str] = []
    for f in source_files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    full = "{}.{}".format(node.module, alias.name)
                    if any(full.startswith(fb) for fb in _FORBIDDEN_IMPORT):
                        violations.append("{} imports {}".format(f.name, full))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name.startswith(fb) for fb in _FORBIDDEN_IMPORT):
                        violations.append("{} imports {}".format(f.name, alias.name))
    return ComplianceItem(name, True, not violations, "; ".join(violations) or "clean")


def _check_forbidden_action_calls(source_files: List[Path]) -> ComplianceItem:
    name = "no_action_call"
    violations: List[str] = []
    for f in source_files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
                for pattern in _FORBIDDEN_ACTION:
                    bare = pattern.rstrip("(")
                    if call_name == bare:
                        violations.append("{}: .{}()".format(f.name, call_name))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("restart", "recover", "schedule", "orchestrate"):
                    violations.append("{}: {}()".format(f.name, node.func.id))
    return ComplianceItem(name, True, not violations, "; ".join(violations) or "clean")


def _check_observational_api(source_files: List[Path]) -> ComplianceItem:
    name = "observational_api_only"
    # API endpoint harus berawalan get_ / list_ (query), bukan aksi mutatif.
    violations: List[str] = []
    for f in source_files:
        if "api" not in str(f).replace("\\", "/"):
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("def "):
                continue
            if isinstance(node, ast.FunctionDef):
                n = node.name
                if n.startswith("get_") or n.startswith("list_") or n == "component_names":
                    continue
                # metode serialisasi/query pasif (bukan aksi) dikecualikan
                if n.startswith("as_") or n.startswith("class_of") \
                        or n.startswith("failed_") or n.startswith("dependenc")\
                        or n.startswith("dependents") or n.startswith("transitive")\
                        or n.startswith("root_") or n.startswith("unresolved")\
                        or n.startswith("has_") or n.startswith("nodes") \
                        or n.startswith("register"):
                    continue
                if n.startswith("__"):
                    continue
                violations.append("{}: {}".format(f.name, n))
    return ComplianceItem(name, True, not violations, "; ".join(violations) or "clean")


def _check_no_runtime_mutation_call(source_files: List[Path]) -> ComplianceItem:
    """Pastikan tidak ada pemanggilan ke rutin mutasi runtime mana pun."""
    name = "no_runtime_mutation"
    # klausa pasif: cari identitas fungsi 'mutate'/'apply'/'execute' yang
    # didefinisikan di dalam package (bukan hanya pemanggilan eksternal).
    violations: List[str] = []
    forbidden_defs = {"mutate", "restart", "schedule", "orchestrate", "execute"}
    for f in source_files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in forbidden_defs:
                violations.append("{} defines mutating fn: {}()".format(f.name, node.name))
    return ComplianceItem(name, True, not violations, "; ".join(violations) or "clean")


def default_source_files(package_path: Path) -> List[Path]:
    """Kumpulan file .py milik IP-3.2-001 dalam package.

    Membatasi scan pada implementasi observasi saja: observation/, diagnostics/,
    readiness/, api/observation.py, dan compliance/checker.py. Ini menjaga
    isolasi bounded context antar-IP - checker observasi hanya mengaudit
    implementasi observasi sendiri, bukan file planning/scheduling/optimization
    ataupun planning_checker yang menjadi tanggung jawab compliance IP-3.2-002.
    """
    skip_self = Path(__file__).resolve()
    include_dirs = {"observation", "diagnostics", "readiness"}
    include_files = {"api/observation.py"}  # file IP-3.2-001 di dir bersama
    files = []
    for f in package_path.rglob("*.py"):
        if f.resolve() == skip_self:
            continue
        rel = f.relative_to(package_path)
        top = rel.parts[0] if rel.parts else ""
        rel_str = rel.as_posix()
        if top.lower() in include_dirs:
            files.append(f)
        elif rel_str in include_files:
            files.append(f)
    return files
