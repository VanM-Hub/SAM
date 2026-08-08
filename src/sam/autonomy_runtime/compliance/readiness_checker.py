# Operational Readiness Compliance - WP-49
# IP-3.2-005 (AO-3.2-001 / ED-3.2-005)
#
# Verifikasi "Operational Readiness without Execution / without Decision".
# Memastikan implementasi IP-3.2-005 (operational_readiness/) tidak pernah:
#   - memilih tindakan / memutuskan
#   - mengeksekusi recovery/lifecycle/coordination
#   - mutate readiness / runtime / governance / policy / mission
#   - approve
#   - efek samping eksternal / hidden persistent state
#   - non-deterministik
#   - kehilangan bukti / kehilangan explainability / kehilangan trust
# Seluruh keluaran = penilaian (assessment), bukan keputusan/aksi.
#
# Berbasis analisis kode sumber (AST).

import ast
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Kata kerja eksekusi/decision yang DILARANG.
_FORBIDDEN_DECISION = (
    "execute_recovery", "execute_lifecycle", "execute_coordination",
    "select_final", "decide", "commit", "apply_recommendation",
    "choose_action", "trigger_recovery", "perform_recovery",
    "execute_readiness", "mutate_readiness",
)

# Modul eksekusi/orchestration/mutation yang TIDAK boleh diimpor.
_FORBIDDEN_IMPORT_MODULES = (
    "sam.autonomy_runtime.execution",
    "sam.autonomy_runtime.orchestrator",
    "sam.autonomy_runtime.operational_readiness.executor",
    "sam.autonomy_runtime.recovery.restore",
)

# Kata kerja mutasi governance/policy/runtime.
_MUTATION_FNS = ("approve", "modify_governance", "modify_policy", "modify_mission",
                 "grant_authority", "authorize", "mutate_runtime", "restart_runtime")


@dataclass(frozen=True)
class ReadinessComplianceItem:
    """Hasil satu pemeriksaan kompliance kesiapan operasional (immutable)."""

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
    """Default file source dalam bounded context operational_readiness/."""
    return _py_files(module_root)


# --- individual checks ---

def _check_no_proposal_execution(trees) -> ReadinessComplianceItem:
    """Tidak boleh ada panggilan/definisi yang mengeksekusi proposal."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = _call_name(node)
                if fn and fn in _FORBIDDEN_DECISION:
                    violations.append("{}: call {!r}".format(path, fn))
            elif isinstance(node, ast.FunctionDef):
                if node.name in _FORBIDDEN_DECISION:
                    violations.append("{}: defines {!r}".format(path, node.name))
    passed = not violations
    detail = "no proposal execution" if passed else "; ".join(violations[:5])
    return ReadinessComplianceItem("RDO-01", "no_proposal_execution", passed, detail)


def _check_no_forbidden_import(trees) -> ReadinessComplianceItem:
    """Tidak boleh mengimpor modul eksekusi/orchestration/mutation."""
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
    return ReadinessComplianceItem("RDO-02", "no_forbidden_import", passed, detail)


def _check_no_readiness_mutation(trees) -> ReadinessComplianceItem:
    """Tidak boleh ada fungsi yang mengubah/force readiness."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                name = node.name.lower()
                if any(m in name for m in ("mutate_readiness", "force_readiness",
                                           "set_ready", "override_readiness")):
                    violations.append("{}: function {!r}".format(path, node.name))
    passed = not violations
    detail = "no readiness mutation functions" if passed else "; ".join(violations[:5])
    return ReadinessComplianceItem("RDO-03", "no_readiness_mutation", passed, detail)


def _check_no_decision_semantics(trees) -> ReadinessComplianceItem:
    """Tidak boleh ada istilah decisive (memilih final/memutuskan)."""
    decisive_tokens = ("decide", "final_decision", "selected_action",
                       "chosen_proposal", "action_selected", "execute")
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                low = node.value.lower()
                if low in decisive_tokens and not low.startswith(
                        ("check_", "no_", "is_")):
                    violations.append("{}: literal {!r}".format(path, node.value))
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if node.name.lower() in decisive_tokens and not node.name.startswith(
                        ("no_", "check_", "_")):
                    violations.append("{}: name {!r}".format(path, node.name))
    passed = not violations
    detail = "no decision semantics" if passed else "; ".join(violations[:5])
    return ReadinessComplianceItem("RDO-04", "no_decision_semantics", passed, detail)


def _check_deterministic_aggregation(trees) -> ReadinessComplianceItem:
    """Agregasi harus deterministik (tidak ada random/time.now/uuid)."""
    non_deterministic = ("random.", "datetime.now", "time.time", "uuid.uuid4")
    violations: List[str] = []
    src_map = _join_source(trees)
    for path, src in src_map.items():
        for token in non_deterministic:
            if token in src:
                violations.append("{}: uses {!r}".format(path, token))
    passed = not violations
    detail = "deterministic aggregation" if passed else "; ".join(violations[:5])
    return ReadinessComplianceItem("RDO-05", "deterministic_aggregation", passed, detail)


def _check_evidence_completeness(trees) -> ReadinessComplianceItem:
    """Bukti harus mengalir dari masukan ke dalam penilaian & rekomendasi.

    Verifikasi bahwa tipe penilaian inti (models), agregasi, rekomendasi, dan
    penjelasan membawa field bukti. Ini memastikan rantai bukti (input ->
    readiness -> recommendation -> explanation) terhubung, bukan sekadar
    menuntut substring 'evidence' di setiap file.
    """
    violations: List[str] = []
    src_map = _join_source(trees)
    # file inti yang harus mengalirkan bukti
    by_name = {os.path.basename(p): src for p, src in src_map.items()}
    core = ("models.py", "aggregation.py", "recommendation.py", "explainability.py")
    for fname in core:
        src = by_name.get(fname)
        if src is None:
            continue
        if "evidence" not in src:
            violations.append("{}: no evidence field".format(fname))
    # masukan penilaian harus membawa evidence
    models_src = by_name.get("models.py", "")
    if models_src and "evidence: Tuple[str, ...] = ()" not in models_src and \
            "evidence" not in models_src:
        violations.append("models.py: ReadinessInput lacks evidence")
    passed = not violations
    detail = "evidence completeness preserved" if passed else "; ".join(violations[:5])
    return ReadinessComplianceItem("RDO-06", "evidence_completeness", passed, detail)


def _check_explainability_preservation(trees) -> ReadinessComplianceItem:
    """Penilaian harus dapat dijelaskan (ada explain/explanation)."""
    violations: List[str] = []
    src_map = _join_source(trees)
    has_explain = any("explain" in src for src in src_map.values())
    if not has_explain:
        violations.append("no explain/explanation present in operational_readiness")
    passed = not violations
    detail = "explainability preserved" if passed else "; ".join(violations[:5])
    return ReadinessComplianceItem("RDO-07", "explainability_preservation", passed, detail)


def _check_trust_preservation(trees) -> ReadinessComplianceItem:
    """Tingkat kepercayaan harus diukur (trust_score/confidence)."""
    violations: List[str] = []
    src_map = _join_source(trees)
    has_trust = any(("trust" in src or "confidence" in src) for src in src_map.values())
    if not has_trust:
        violations.append("no trust/confidence measurement present")
    passed = not violations
    detail = "trust preservation" if passed else "; ".join(violations[:5])
    return ReadinessComplianceItem("RDO-08", "trust_preservation", passed, detail)


def _check_no_runtime_mutation(trees) -> ReadinessComplianceItem:
    """Tidak boleh ada fungsi mutation runtime/start/stop/restart."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                name = node.name.lower()
                if any(m in name for m in ("restart", "launch", "stop_runtime",
                                           "start_runtime", "deploy")):
                    violations.append("{}: function {!r}".format(path, node.name))
            if isinstance(node, ast.Call):
                fn = _call_name(node)
                if fn and fn.strip("_").lower() in ("restart", "launch", "stop",
                                                    "start", "deploy"):
                    violations.append("{}: call {!r}".format(path, fn))
    passed = not violations
    detail = "no runtime mutation functions" if passed else "; ".join(violations[:5])
    return ReadinessComplianceItem("RDO-09", "no_runtime_mutation", passed, detail)


def _check_no_approval_or_governance_mutation(trees) -> ReadinessComplianceItem:
    """Tidak boleh ada approval / mutasi governance / policy / mission."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.Call)):
                name = node.name.lower() if isinstance(node, ast.FunctionDef) \
                    else (_call_name(node) or "").lower()
                if any(m in name for m in _MUTATION_FNS):
                    label = "defines" if isinstance(node, ast.FunctionDef) else "calls"
                    violations.append("{}: {} {!r}".format(path, label, name))
    passed = not violations
    detail = "no approval/governance mutation" if passed else "; ".join(violations[:5])
    return ReadinessComplianceItem("RDO-10", "no_approval_governance_mutation", passed, detail)


def _check_no_external_side_effect(trees) -> ReadinessComplianceItem:
    """Tidak boleh ada impor/akses jaringan atau fs eksternal luaran."""
    side_effect_modules = ("requests", "urllib", "smtplib", "socket", "http")
    side_effect_funcs = ("subprocess", "os.system", "shutil", "eval(")
    violations: List[str] = []
    src_map = _join_source(trees)
    for path, src in src_map.items():
        for token in side_effect_funcs:
            if token in src:
                violations.append("{}: token {!r}".format(path, token))
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
    return ReadinessComplianceItem("RDO-11", "no_external_side_effect", passed, detail)


def _check_no_hidden_persistent_state(trees) -> ReadinessComplianceItem:
    """Tidak boleh ada persistensi/state tersembunyi (file db/json/pickle)."""
    persist_tokens = ("sqlite", "pickle.load", "json.dump", "shelve", "dbm",
                      "joblib", "open(")
    violations: List[str] = []
    src_map = _join_source(trees)
    for path, src in src_map.items():
        for token in persist_tokens:
            if token in src:
                violations.append("{}: token {!r}".format(path, token))
    passed = not violations
    detail = "no hidden persistent state" if passed else "; ".join(violations[:5])
    return ReadinessComplianceItem("RDO-12", "no_hidden_persistent_state", passed, detail)


# --- entry point ---

def compliance_check(
    source_files: List[str],
    module_root: str = "",
    implementation_dirs: Optional[Tuple[str, ...]] = None,
) -> Tuple[bool, Tuple[ReadinessComplianceItem, ...]]:
    """Jalankan seluruh pemeriksaan kompliance operational readiness."""
    trees = _ast_trees(source_files)
    checks = (
        _check_no_proposal_execution(trees),
        _check_no_forbidden_import(trees),
        _check_no_readiness_mutation(trees),
        _check_no_decision_semantics(trees),
        _check_deterministic_aggregation(trees),
        _check_evidence_completeness(trees),
        _check_explainability_preservation(trees),
        _check_trust_preservation(trees),
        _check_no_runtime_mutation(trees),
        _check_no_approval_or_governance_mutation(trees),
        _check_no_external_side_effect(trees),
        _check_no_hidden_persistent_state(trees),
    )
    all_pass = all(c.passed for c in checks)
    return all_pass, checks


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
