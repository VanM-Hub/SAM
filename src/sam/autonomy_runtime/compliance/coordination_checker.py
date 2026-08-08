# Coordination & Lifecycle Compliance - WP-39
# IP-3.2-004 (AO-3.2-001 / ED-3.2-004)
#
# Verifikasi "coordination without orchestration" & "lifecycle proposal vs
# lifecycle mutation". Memastikan implementasi IP-3.2-004 (coordination/,
# lifecycle/) tidak pernah:
#   - orchestrate / dispatch / trigger eksekusi runtime lain
#   - start/stop/restart runtime
#   - mengubah status lifecycle aktual (mutasi)
#   - approve / mutasi governance
#   - efek samping eksternal / hidden persistent state
#   - koordinasi/lifecycle non-deterministik
# Seluruh keluaran = model & proposal, bukan aksi.
#
# Berbasis analisis kode sumber (AST).

import ast
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Kata kerja orchestration/eksekusi runtime yang DILARANG.
_FORBIDDEN_ORCHESTRATION = (
    "orchestrate", "dispatch", "trigger_runtime", "start_runtime",
    "stop_runtime", "restart_runtime", "launch_runtime", "deploy_runtime",
    "transition_lifecycle", "apply_lifecycle", "mutate_lifecycle",
)

# Modul eksekusi/orchestration yang TIDAK boleh diimpor.
_FORBIDDEN_IMPORT_MODULES = (
    "sam.autonomy_runtime.execution",
    "sam.autonomy_runtime.orchestrator",
    "sam.autonomy_runtime.coordination.executor",
    "sam.autonomy_runtime.lifecycle.executor",
)

# Kata kerja mutasi keras / lifecycle mutation.
_LIFECYCLE_MUTATION_FNS = (
    "start", "stop", "restart", "apply_lifecycle", "transition_lifecycle",
    "set_stage", "force_stage", "mutate_stage", "persist_lifecycle",
)


@dataclass(frozen=True)
class CoordinationComplianceItem:
    """Hasil satu pemeriksaan kompliance koordinasi & lifecycle (immutable)."""

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
    """Default file source dalam bounded context coordination/ + lifecycle/."""
    return _py_files(module_root)


def compliance_check(
    source_files: List[str],
    module_root: str = "",
    implementation_dirs: Optional[Tuple[str, ...]] = None,
) -> Tuple[bool, Tuple[CoordinationComplianceItem, ...]]:
    """Jalankan seluruh pemeriksaan kompliance coordination-without-orchestration."""
    trees = _ast_trees(source_files)
    checks = (
        _check_no_orchestration(trees),
        _check_no_forbidden_import(trees),
        _check_no_runtime_mutation(trees),
        _check_no_lifecycle_mutation(trees),
        _check_proposal_only_names(trees),
        _check_no_approval_or_governance_mutation(trees),
        _check_no_external_side_effect(trees),
        _check_no_hidden_persistent_state(trees),
        _check_deterministic(trees),
    )
    all_pass = all(c.passed for c in checks)
    return all_pass, checks


# --- individual checks ---

def _check_no_orchestration(trees) -> CoordinationComplianceItem:
    """Tidak boleh ada panggilan/definisi orchestration/dispatch/ekseskusi."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = _call_name(node)
                if fn and fn in _FORBIDDEN_ORCHESTRATION:
                    violations.append("{}: call {!r}".format(path, fn))
            elif isinstance(node, ast.FunctionDef):
                if node.name in _FORBIDDEN_ORCHESTRATION:
                    violations.append("{}: defines {!r}".format(path, node.name))
    passed = not violations
    detail = "no orchestration/dispatch" if passed else "; ".join(violations[:5])
    return CoordinationComplianceItem("CRD-01", "no_orchestration", passed, detail)


def _check_no_forbidden_import(trees) -> CoordinationComplianceItem:
    """Tidak boleh mengimpor modul orchestration/execution eksternal."""
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
    return CoordinationComplianceItem("CRD-02", "no_forbidden_import", passed, detail)


def _check_no_runtime_mutation(trees) -> CoordinationComplianceItem:
    """Tidak boleh ada definisi fungsi mutasi Runtime eksternal."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                name = node.name.lower()
                if any(m in name for m in ("restart", "launch", "deploy", "execute")) and \
                   not name.startswith(("coordinate_", "lifecycle_", "plan_")):
                    violations.append("{}: function {!r}".format(path, node.name))
    passed = not violations
    detail = "no runtime mutation functions" if passed else "; ".join(violations[:5])
    return CoordinationComplianceItem("CRD-03", "no_runtime_mutation", passed, detail)


def _check_no_lifecycle_mutation(trees) -> CoordinationComplianceItem:
    """Tidak boleh ada fungsi yang memaksa/mengubah status lifecycle aktual."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                name = node.name.lower()
                if any(m in name for m in _LIFECYCLE_MUTATION_FNS) and \
                   not name.startswith(("propose_", "assess_", "plan_", "lifecycle_")):
                    violations.append("{}: function {!r}".format(path, node.name))
    passed = not violations
    detail = "no lifecycle mutation functions" if passed else "; ".join(violations[:5])
    return CoordinationComplianceItem("CRD-04", "no_lifecycle_mutation", passed, detail)


def _check_proposal_only_names(trees) -> CoordinationComplianceItem:
    """Literal aksi nyata tidak boleh muncul sebagai nilai output."""
    literal_bad = ("orchestrate", "dispatch", "start_runtime", "restart",
                   "transition_lifecycle", "mutate_stage")
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                low = node.value.lower()
                if low in literal_bad and \
                   not low.startswith(("coordinate_", "lifecycle_", "plan_", "propose_")):
                    violations.append("{}: literal {!r}".format(path, node.value))
    passed = not violations
    detail = "proposal-only naming enforced" if passed else "; ".join(violations[:5])
    return CoordinationComplianceItem("CRD-05", "proposal_only_names", passed, detail)


def _check_no_approval_or_governance_mutation(trees) -> CoordinationComplianceItem:
    """Tidak boleh ada approval / mutasi governance / policy / mission."""
    tokens = ("approve", "grant_authority", "modify_governance",
              "modify_policy", "modify_mission", "authorize")
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = _call_name(node)
                if fn and fn in tokens:
                    violations.append("{}: call {!r}".format(path, fn))
    passed = not violations
    detail = "no approval/governance mutation" if passed else "; ".join(violations[:5])
    return CoordinationComplianceItem("CRD-06", "no_approval_governance_mutation", passed, detail)


def _check_no_external_side_effect(trees) -> CoordinationComplianceItem:
    """Tidak boleh ada impor/akses jaringan atau fs eksternal luaran."""
    side_effect_modules = ("requests", "urllib", "smtplib", "socket", "http")
    side_effect_funcs = ("open(", "subprocess", "os.system", "shutil", "eval(")
    violations: List[str] = []
    src_map = _join_source(trees)
    for path, src in src_map.items():
        for token in side_effect_funcs:
            if token in src:
                violations.append("{}: token {!r}".format(path, token.rstrip("(")))
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in side_effect_modules:
                        violations.append("{}: import {!r}".format(path, alias.name))
    passed = not violations
    detail = "no external side effect" if passed else "; ".join(violations[:5])
    return CoordinationComplianceItem("CRD-07", "no_external_side_effect", passed, detail)


def _check_no_hidden_persistent_state(trees) -> CoordinationComplianceItem:
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
    return CoordinationComplianceItem("CRD-08", "no_hidden_persistent_state", passed, detail)


def _check_deterministic(trees) -> CoordinationComplianceItem:
    """Koordinasi/lifecycle harus deterministik (tidak ada random/time)."""
    non_deterministic = ("random.", "time.time", "datetime.now", "uuid.uuid4")
    violations: List[str] = []
    src_map = _join_source(trees)
    for path, src in src_map.items():
        for token in non_deterministic:
            if token in src:
                violations.append("{}: uses {!r}".format(path, token))
    passed = not violations
    detail = "deterministic coordination analysis" if passed else "; ".join(violations[:5])
    return CoordinationComplianceItem("CRD-09", "deterministic", passed, detail)


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
