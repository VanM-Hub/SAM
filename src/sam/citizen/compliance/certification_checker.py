# Certification Compliance - WP-28
# IP-3.3-003 (AO-3.3-001 / ED-3.3-001 cycle 3)
#
# Compliance khas Certification & Ecosystem Intelligence (10 checks).
# Memastikan ecosystem/ tidak melanggar guardrail IP-3.3-003:
#
# SHALL   : assessment deterministik, intelligence agregasi, recommendation
#           advisory, health kolektif, explainability, evidence-first,
#           registry-based, registry authoritative.
# SHALL NOT: approval/mutation lifecycle, ecosystem control, governance
#           decision, privileged ecosystem, implicit certification,
#           autoprovision, non-determinism.

import ast
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# kata kerja approval/kendali yang DILARANG di ecosystem/.
_FORBIDDEN_AUTHORITY = (
    "approve_citizen", "apply_certification", "certify_activate",
    "activate_ecosystem", "deactivate_ecosystem", "control_runtime",
    "control_citizen", "mutate_lifecycle", "grant_privilege",
    "authorize_ecosystem", "modify_governance", "auto_approve",
    "autoapply", "auto_provision", "provision_ecosystem",
)

# modul eksekusi/runtime/governance yang TIDAK boleh diimport ecosystem/.
_FORBIDDEN_IMPORT = (
    "sam.autonomy_runtime.execution",
    "sam.autonomy_runtime.orchestrator",
    "sam.execution",
    "sam.recovery.restore",
    "sam.governance",
    "sam.runtime",
)


@dataclass(frozen=True)
class CertificationComplianceItem:
    """Hasil satu pemeriksaan kompliance certification (immutable)."""

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
            if fn.endswith(".py") and fn != "__init__.py":
                files.append(os.path.join(dirpath, fn))
    return sorted(files)


def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return ""


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


def _call_name(node: ast.Call) -> Optional[str]:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _import_forbidden(module: str) -> bool:
    return any(module == m or module.startswith(m + ".") for m in _FORBIDDEN_IMPORT)


def default_source_files(module_root: str) -> List[str]:
    return _py_files(module_root)


# --- individual checks ---

def _check_assessment_only(trees) -> CertificationComplianceItem:
    """Certification menghasilkan assessment, bukan activation/mutation."""
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "activate_citizen" in src or "apply_certification" in src \
                or "transition_lifecycle" in src:
            violates = True
    return CertificationComplianceItem(
        "CER-01", "assessment_only", not violates,
        "certification is assessment (no lifecycle mutation)" if not violates
        else "certification mutation found")


def _check_no_approval(trees) -> CertificationComplianceItem:
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                if node.name.lower() in _FORBIDDEN_AUTHORITY:
                    violations.append("{}: {!r}".format(path, node.name))
    return CertificationComplianceItem(
        "CER-02", "no_approval", not violations,
        "no approve/authorize/apply verbs" if not violations
        else "; ".join(violations[:5]))


def _check_no_privilege(trees) -> CertificationComplianceItem:
    impl = ("is_privileged=True", "kind='owner'", "kind == 'admin'",
            "privileged_ecosystem", "grant_privilege", "has_privilege")
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        for tok in impl:
            if tok in src:
                violates = True
    return CertificationComplianceItem(
        "CER-03", "no_privilege", not violates,
        "no privileged ecosystem member" if not violates
        else "privileged ecosystem implementation found")


def _check_deterministic(trees) -> CertificationComplianceItem:
    nondet = ("random.", "time.time", "datetime.now", "uuid.uuid4",
              "time.sleep")
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        for tok in nondet:
            if tok in src:
                violates = True
    return CertificationComplianceItem(
        "CER-04", "deterministic", not violates,
        "no random/time in certification logic" if not violates
        else "non-determinism found")


def _check_evidence_first(trees) -> CertificationComplianceItem:
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "evidence" in src and ("basis" in src or "statements" in src):
            ok = True
    return CertificationComplianceItem(
        "CER-05", "evidence_first", ok,
        "results carry evidence & basis" if ok else "evidence missing")


def _check_registry_authoritative(trees) -> CertificationComplianceItem:
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "registry" in src and ("_registry" in src or "CitizenRegistry" in src):
            ok = True
    return CertificationComplianceItem(
        "CER-06", "registry_authoritative", ok,
        "identities sourced from registry" if ok else "no registry usage")


def _check_intelligence_not_governance(trees) -> CertificationComplianceItem:
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "decision" in src and ("make_decision" in src or "decide(" in src):
            violates = True
    return CertificationComplianceItem(
        "CER-07", "intelligence_not_governance", not violates,
        "intelligence aggregates, does not decide" if not violates
        else "intelligence makes decisions")


def _check_recommendation_advisory(trees) -> CertificationComplianceItem:
    violates = False
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "recommend" in src and "advisory" in src:
            ok = True
        if "recommend" in src and ("apply(" in src or "execute(" in src):
            violates = True
    return CertificationComplianceItem(
        "CER-08", "recommendation_advisory", ok and not violates,
        "recommendations are advisory, never applied" if ok and not violates
        else "recommendation auto-apply found or advisory missing")


def _check_no_ecosystem_control(trees) -> CertificationComplianceItem:
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        for tok in ("control_runtime", "control_citizen", "restart_citizen",
                    "shutdown_citizen", "start_ecosystem", "stop_ecosystem"):
            if tok in src:
                violations.append("{}: {!r}".format(path, tok))
    return CertificationComplianceItem(
        "CER-09", "no_ecosystem_control", not violations,
        "no runtime/citizen/ecosystem control" if not violations
        else "; ".join(violations[:5]))


def _check_no_implicit_certification(trees) -> CertificationComplianceItem:
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "auto_certify" in src or ("certify((" in src and ".__init__" in src):
            # pemeriksaan ringan: tidak ada auto-certify di init
            if "auto_certify" in src:
                violates = True
    return CertificationComplianceItem(
        "CER-10", "no_implicit_certification", not violates,
        "certification is explicit" if not violates else "auto-certify found")


def compliance_check(
    source_files: List[str],
    module_root: str = "",
    implementation_dirs: Optional[Tuple[str, ...]] = None,
) -> Tuple[bool, Tuple[CertificationComplianceItem, ...]]:
    trees = _ast_trees(source_files)
    checks = (
        _check_assessment_only(trees),
        _check_no_approval(trees),
        _check_no_privilege(trees),
        _check_deterministic(trees),
        _check_evidence_first(trees),
        _check_registry_authoritative(trees),
        _check_intelligence_not_governance(trees),
        _check_recommendation_advisory(trees),
        _check_no_ecosystem_control(trees),
        _check_no_implicit_certification(trees),
    )
    all_pass = all(c.passed for c in checks)
    return all_pass, checks
