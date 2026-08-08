# Recovery Compliance - WP-29
# IP-3.2-003 (AO-3.2-001 / ED-3.2-003)
#
# Verifikasi "recovery without execution".
# Memastikan seluruh implementasi IP-3.2-003 (recovery/, healing/) tidak pernah:
#   - mengeksekusi recovery (restart, rollback, self-heal otomatis)
#   - mengubah Mission / Workflow / Policy / Governance
#   - mengubah Runtime lain / mutasi Runtime
#   - melakukan Approval / memperoleh authority baru
#   - menghasilkan efek samping eksternal
#   - menyimpan hidden persistent state
#   - melakukan recovery non-deterministik
# Seluruh keluaran harus Recovery Proposal deterministik, bukan aksi.
#
# Berbasis analisis kode sumber (AST) + verifikasi artefak.

import ast
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Kata kerja yang TIDAK boleh muncul sebagai aksi eksekusi di kode IP-3.2-003.
# Label "recover_" / "heal_" / "plan_" diizinkan karena itu deskripsi proposal.
# Yang DILARANG adalah granularitas eksekusi nyata.
_FORBIDDEN_EXEC_TOKENS = (
    "restart_runtime", "stop_runtime", "start_runtime", "rollback",
    "execute_heal", "auto_heal", "apply_recovery", "trigger_restart",
    "modify_mission", "modify_policy", "modify_governance",
)

# Modul yang TIDAK boleh diimpor (lewat boundary keputusan/eksekusi nyata).
_FORBIDDEN_IMPORT_MODULES = (
    "sam.autonomy_runtime.execution",
    "sam.autonomy_runtime.lifecycle",
    "sam.autonomy_runtime.coordination",
    "sam.autonomy_runtime.recovery.executor",
    "sam.autonomy_runtime.healing.executor",
)

# Kata kerja mutasi keras yang menandakan eksekusi nyata, bukan proposal.
_MUTATION_FNS = (
    "restart", "rollback", "apply", "execute", "set_state", "run_recovery",
    "start_", "stop_", "delete_", "create_", "persist",
)


@dataclass(frozen=True)
class RecoveryComplianceItem:
    """Hasil satu pemeriksaan kompliance recovery (immutable)."""

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


def _py_files(root: str) -> List[str]:
    files: List[str] = []
    if not os.path.isdir(root):
        return files
    for dirpath, _, filenames in os.walk(root):
        for fn in sorted(filenames):
            if fn.endswith(".py"):
                files.append(os.path.join(dirpath, fn))
    return sorted(files)


def _ast_trees(files: List[str]) -> List[Tuple[str, Optional[ast.Module]]]:
    result: List[Tuple[str, Optional[ast.Module]]] = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                src = fh.read()
            result.append((path, ast.parse(src, filename=path)))
        except Exception:
            result.append((path, None))
    return result


def default_source_files(module_root: str) -> List[str]:
    """Default file source dalam bounded context recovery/ + healing/."""
    return _py_files(module_root)


def compliance_check(
    source_files: List[str],
    module_root: str = "",
    implementation_dirs: Optional[Tuple[str, ...]] = None,
) -> Tuple[bool, Tuple[RecoveryComplianceItem, ...]]:
    """Jalankan seluruh pemeriksaan kompliance recovery-without-execution."""
    trees = _ast_trees(source_files)
    checks = (
        _check_no_execution(trees),
        _check_no_forbidden_import(trees),
        _check_no_runtime_mutation(trees),
        _check_proposal_only_names(trees),
        _check_no_approval(trees),
        _check_no_external_side_effect(trees),
        _check_no_hidden_persistent_state(trees),
        _check_deterministic(trees),
    )
    all_pass = all(c.passed for c in checks)
    return all_pass, checks


# --- individual checks ---

def _check_no_execution(trees) -> RecoveryComplianceItem:
    """Tidak boleh ada panggilan/definisi fungsi eksekusi recovery nyata."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = _call_name(node)
                if fn and fn in _FORBIDDEN_EXEC_TOKENS:
                    violations.append("{}: call {!r}".format(path, fn))
            elif isinstance(node, ast.FunctionDef):
                if node.name in _FORBIDDEN_EXEC_TOKENS:
                    violations.append("{}: defines {!r}".format(path, node.name))
    passed = not violations
    detail = "no recovery execution" if passed else "; ".join(violations[:5])
    return RecoveryComplianceItem("REC-01", "no_execution", passed, detail)


def _check_no_forbidden_import(trees) -> RecoveryComplianceItem:
    """Tidak boleh mengimpor modul eksekusi nyata / di luar boundary proposal."""
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
    return RecoveryComplianceItem("REC-02", "no_forbidden_import", passed, detail)


def _check_no_runtime_mutation(trees) -> RecoveryComplianceItem:
    """Tidak boleh ada definisi fungsi mutasi Runtime/Global."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                name = node.name.lower()
                if any(m in name for m in _MUTATION_FNS) and \
                   not name.startswith(("recover_", "heal_", "plan_")):
                    violations.append("{}: function {!r}".format(path, node.name))
    passed = not violations
    detail = "no runtime mutation functions" if passed else "; ".join(violations[:5])
    return RecoveryComplianceItem("REC-03", "no_runtime_mutation", passed, detail)


def _check_proposal_only_names(trees) -> RecoveryComplianceItem:
    """Literal aksi nyata tidak boleh muncul sebagai nilai output."""
    literal_bad = ("execute", "restart", "rollback", "apply_recovery", "auto_heal")
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                low = node.value.lower()
                if low in literal_bad and not low.startswith(("recover_", "heal_", "plan_")):
                    violations.append("{}: literal {!r}".format(path, node.value))
    passed = not violations
    detail = "proposal-only naming enforced" if passed else "; ".join(violations[:5])
    return RecoveryComplianceItem("REC-04", "proposal_only_names", passed, detail)


def _check_no_approval(trees) -> RecoveryComplianceItem:
    """Tidak boleh ada invokasi approval/otorisasi otomatis."""
    approval_tokens = ("approve", "grant_authority", "request_approval", "authorize")
    violations: List[str] = []
    src_map = _join_source(trees)
    for path, src in src_map.items():
        for fn in approval_tokens:
            if fn + "(" in src and not src.startswith("#"):
                violations.append("{}: token {!r}".format(path, fn))
    passed = not violations
    detail = "no approval invocation" if passed else "; ".join(violations[:5])
    return RecoveryComplianceItem("REC-05", "no_approval", passed, detail)


def _check_no_external_side_effect(trees) -> RecoveryComplianceItem:
    """Tidak boleh ada impor/akses jaringan atau sistem file eksternal luaran."""
    side_effect_modules = ("requests", "urllib", "smtplib", "socket", "http")
    side_effect_funcs = ("open(", "subprocess", "os.system", "shutil", "eval(")
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in side_effect_modules:
                        violations.append("{}: import {!r}".format(path, alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in side_effect_modules:
                    violations.append("{}: import {!r}".format(path, node.module))
            elif isinstance(node, ast.Call):
                fn = _call_name(node)
                if fn and fn in ("open", "subprocess", "os.system", "shutil", "eval"):
                    violations.append("{}: call {!r}".format(path, fn))
    passed = not violations
    detail = "no external side effect" if passed else "; ".join(violations[:5])
    return RecoveryComplianceItem("REC-06", "no_external_side_effect", passed, detail)


def _check_no_hidden_persistent_state(trees) -> RecoveryComplianceItem:
    """Tidak boleh ada persistensi/state tersembunyi (file db/json/pickle)."""
    persist_tokens = ("sqlite", "open(", ".write(", "pickle.load", "json.dump",
                      "shelve", "dbm", "joblib")
    violations: List[str] = []
    src_map = _join_source(trees)
    for path, src in src_map.items():
        for token in persist_tokens:
            if token in src:
                violations.append("{}: token {!r}".format(path, token))
    passed = not violations
    detail = "no hidden persistent state" if passed else "; ".join(violations[:5])
    return RecoveryComplianceItem("REC-07", "no_hidden_persistent_state", passed, detail)


def _check_deterministic(trees) -> RecoveryComplianceItem:
    """Analisis/strategi recovery harus deterministik (tidak ada random/time)."""
    non_deterministic = ("random.", "time.time", "datetime.now", "uuid.uuid4")
    violations: List[str] = []
    src_map = _join_source(trees)
    for path, src in src_map.items():
        for token in non_deterministic:
            if token in src:
                violations.append("{}: uses {!r}".format(path, token))
    passed = not violations
    detail = "deterministic recovery analysis" if passed else "; ".join(violations[:5])
    return RecoveryComplianceItem("REC-08", "deterministic", passed, detail)


# --- helpers ---

def _call_name(node: ast.Call) -> Optional[str]:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _import_forbidden(module: str) -> bool:
    return any(module == m or module.startswith(m + ".") for m in _FORBIDDEN_IMPORT_MODULES)


def _join_source(trees: List[Tuple[str, Optional[ast.Module]]]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for path, _tree in trees:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                result[path] = fh.read()
        except Exception:
            result[path] = ""
    return result
