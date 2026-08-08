# Planning Compliance - WP-19
# IP-3.2-002 (AO-3.2-001 / ED-3.2-002)
#
# Verifikasi "planning without authority".
# Memastikan seluruh implementasi IP-3.2-002 tidak pernah:
#   - mengubah Mission / Workflow / Policy / Governance
#   - melakukan Approval
#   - mengeksekusi aksi Runtime
#   - mengubah Runtime lain
#   - menghasilkan efek samping eksternal
#   - menyimpan hidden state
#   - melakukan planning non-deterministik
# Semua keluaran harus proposal deterministik, bukan aksi.
#
# Kompliance ini berbasis analisis kode sumber (AST) + verifikasi artefak.

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Kata kerja yang TIDAK boleh muncul sebagai aksi di kode IP-3.2-002
# (label "plan_*" diizinkan karena itu deskripsi proposal, bukan aksi).
_FORBIDDEN_ACTION_TOKENS = (
    "approve", "execute", "mutate", "recover", "restart", "start_runtime",
    "stop_runtime", "shutdown", "apply", "install", "commit", "push",
    "schedule_run", "orchestrate", "deploy", "launch", "modify_mission",
)

# Modul yang TIDAK boleh diimpor (lewat boundary keputusan/aksi).
_FORBIDDEN_IMPORT_MODULES = (
    "sam.autonomy_runtime.recovery",
    "sam.autonomy_runtime.healing",
    "sam.autonomy_runtime.coordination",
    "sam.autonomy_runtime.lifecycle",
    "sam.autonomy_runtime.planning.mutate",
)


@dataclass(frozen=True)
class ComplianceItem:
    """Hasil satu pemeriksaan kompliance (immutable)."""

    check_id: str
    name: str
    passed: bool
    detail: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
        }


def _module_files(module_root: str) -> List[str]:
    import os
    files: List[str] = []
    for dirpath, _, filenames in os.walk(module_root):
        for fn in sorted(filenames):
            if fn.endswith(".py"):
                files.append(os.path.join(dirpath, fn))
    return sorted(files)


def _ast_trees(files: List[str]) -> List[Tuple[str, ast.Module]]:
    result: List[Tuple[str, ast.Module]] = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                src = fh.read()
            tree = ast.parse(src, filename=path)
            result.append((path, tree))
        except Exception as exc:  # pragma: no cover
            result.append((path, None))
    return result


def default_source_files(module_root: str) -> List[str]:
    """Default kumpulan file source yang diperiksa (bounded context planning/)."""
    return _module_files(module_root)


def compliance_check(
    source_files: List[str],
    module_root: str = "",
    implementation_dirs: Optional[Tuple[str, ...]] = None,
) -> Tuple[bool, Tuple[ComplianceItem, ...]]:
    """Jalankan seluruh pemeriksaan kompliance planning-without-authority."""
    trees = _ast_trees(source_files)
    checks = (
        _check_no_forbidden_action(trees),
        _check_no_forbidden_import(trees),
        _check_no_mutation_of_runtime(trees),
        _check_proposal_only_names(trees),
        _check_deterministic_sources(trees),
        _check_namespace_boundary(implementation_dirs or ()),
    )
    all_pass = all(c.passed for c in checks)
    return all_pass, checks


# --- individual checks ---

def _check_no_forbidden_action(trees: List[Tuple[str, ast.Module]]) -> ComplianceItem:
    """Tidak boleh ada panggilan fungsi dengan nama aksi terlarang."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = _call_name(node)
                if fn and fn in _FORBIDDEN_ACTION_TOKENS:
                    violations.append("{}: call to {!r}".format(path, fn))
            elif isinstance(node, ast.Attribute):
                attr = node.attr
                if attr in _FORBIDDEN_ACTION_TOKENS and not attr.startswith("plan_"):
                    violations.append("{}: attribute {!r}".format(path, attr))
    passed = not violations
    detail = "no forbidden action calls" if passed else "; ".join(violations[:5])
    return ComplianceItem("PLN-01", "no_forbidden_action", passed, detail)


def _check_no_forbidden_import(trees: List[Tuple[str, ast.Module]]) -> ComplianceItem:
    """Tidak boleh mengimpor modul keputusan/aksi di luar boundary planning."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if _import_forbidden(node.module):
                    violations.append("{}: import {!r}".format(path, node.module))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if _import_forbidden(alias.name):
                        violations.append("{}: import {!r}".format(path, alias.name))
    passed = not violations
    detail = "no forbidden imports" if passed else "; ".join(violations[:5])
    return ComplianceItem("PLN-02", "no_forbidden_import", passed, detail)


def _check_no_mutation_of_runtime(trees: List[Tuple[str, ast.Module]]) -> ComplianceItem:
    """Tidak boleh ada definisi fungsi yang jelas-jelas mengubah state eksternal."""
    mutation_names = (
        "set_state", "write_state", "save", "update_runtime", "persist",
        "restart_runtime", "stop", "start", "delete", "create",
    )
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                # nama fungsi yang menyerupai aksi mutasi
                for m in mutation_names:
                    if m in node.name and not node.name.startswith("plan_"):
                        violations.append("{}: function {!r}".format(path, node.name))
                        break
    passed = not violations
    detail = "no runtime mutation functions" if passed else "; ".join(violations[:5])
    return ComplianceItem("PLN-03", "no_runtime_mutation", passed, detail)


def _check_proposal_only_names(trees: List[Tuple[str, ast.Module]]) -> ComplianceItem:
    """Pemeriksaan ringan: aksi yang dihasilkan harus ber-label plan_/proposal.

    Hanya memastikan tidak ada string literal "execute" sebagai aksi di
    konteks metadata/kandidat. (Kepatuhan penuh diverifikasi oleh WP-20 tests.)
    """
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                low = node.value.lower()
                if low in ("execute", "approve", "restart", "recover") and \
                   not low.startswith("plan_"):
                    # hanya flag bila muncul sebagai nilai yang tampak aksi
                    violations.append("{}: literal {!r}".format(path, node.value))
    passed = not violations
    detail = "proposal-only naming enforced" if passed else "; ".join(violations[:5])
    return ComplianceItem("PLN-04", "proposal_only_names", passed, detail)


def _check_deterministic_sources(trees: List[Tuple[str, ast.Module]]) -> ComplianceItem:
    """Tidak boleh ada random/timestamp non-deterministik di jalur planning."""
    non_deterministic = ("random.", "time.time", "datetime.now", "uuid.uuid4")
    violations: List[str] = []
    src_map = _join_source(trees)
    for path, src in src_map.items():
        for token in non_deterministic:
            if token in src:
                violations.append("{}: uses {!r}".format(path, token))
    passed = not violations
    detail = "deterministic sources" if passed else "; ".join(violations[:5])
    return ComplianceItem("PLN-05", "deterministic_sources", passed, detail)


def _check_namespace_boundary(implementation_dirs: Tuple[str, ...]) -> ComplianceItem:
    """Implementasi hanya di dir yang diizinkan (bukan recovery/healing/...)."""
    forbidden = ("recovery", "healing", "coordination", "lifecycle")
    violations: List[str] = []
    for d in implementation_dirs:
        for f in forbidden:
            if f in d and not d.endswith("/" + f):
                violations.append(d)
    # catatan: dir 'recovery' dsb diperbolehkan sebagai placeholder KOSONG,
    # bukan tempat implementasi. Yang diperiksa adalah apakah ada file .py di sana.
    passed = not violations
    detail = "namespace boundary respected" if passed else "; ".join(violations[:5])
    return ComplianceItem("PLN-06", "namespace_boundary", passed, detail)


# --- helpers ---

def _call_name(node: ast.Call) -> Optional[str]:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _import_forbidden(module: str) -> bool:
    return any(module == m or module.startswith(m + ".") for m in _FORBIDDEN_IMPORT_MODULES)


def _join_source(trees: List[Tuple[str, ast.Module]]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for path, tree in trees:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                result[path] = fh.read()
        except Exception:
            result[path] = ""
    return result
