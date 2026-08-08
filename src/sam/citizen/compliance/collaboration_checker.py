# Collaboration Compliance - WP-18
# IP-3.3-002 (AO-3.3-001 / ED-3.3-001 2nd cycle)
#
# Compliance khas Collaboration & Compatibility (10 checks). Memastikan
# bounded context collaborasi tidak melanggar guardrail IP-3.3-002:
#
# SHALL   : proposal deterministik, compatibility penilaian, contract
#           resolution lookup, dependency analysis, explainability, 
#           privilege-free kolaborasi, Citizen Equality.
# SHALL NOT: orchestration/eksekusi kolaborasi, authority acquisition,
#           implicit collaboration, mutation runtime/governance/foundation,
#           privileged citizen, non-determinism.

import ast
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# kata kerja eksekusi/otoritas yang DILARANG di collaboration/.
_FORBIDDEN_AUTHORITY = (
    "activate_channel", "deactivate_channel", "run_collaboration",
    "execute_collaboration", "start_collaboration", "form_collaboration",
    "grant_privilege", "authorize_collaboration", "approve_collaboration",
    "transition_lifecycle", "mutate_runtime", "mutate_governance",
    "orphanize_contract", "force_resolve",
)

# modul eksekusi/orchestration yang TIDAK boleh diimport collaboration/.
_FORBIDDEN_IMPORT = (
    "sam.autonomy_runtime.execution",
    "sam.autonomy_runtime.orchestrator",
    "sam.execution",
    "sam.recovery.restore",
)


@dataclass(frozen=True)
class CollaborationComplianceItem:
    """Hasil satu pemeriksaan kompliance collaboration (immutable)."""

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
    result = []
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

def _check_proposal_only(trees) -> CollaborationComplianceItem:
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "proposal" in src and "is_proposal" in src:
            ok = True
    return CollaborationComplianceItem(
        "COL-01", "proposal_only", ok,
        "proposals marked is_proposal=True" if ok else "no proposal semantics")


def _check_no_orchestration(trees) -> CollaborationComplianceItem:
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                if node.name.lower() in _FORBIDDEN_AUTHORITY:
                    violations.append("{}: defines {!r}".format(path, node.name))
    return CollaborationComplianceItem(
        "COL-02", "no_orchestration", not violations,
        "no collaboration execution verbs" if not violations
        else "; ".join(violations[:5]))


def _check_no_privilege(trees) -> CollaborationComplianceItem:
    impl = ("is_privileged=True", "role='owner'", "role=\"owner\"",
            "role='master'", "role=\"master\"", "role='controller'",
            "role=\"controller\"", "('owner',", "('master',")
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        for tok in impl:
            if tok in src:
                violates = True
    return CollaborationComplianceItem(
        "COL-03", "no_privilege", not violates,
        "privilege-free roles enforced" if not violates
        else "privileged-role implementation found")


def _check_no_implicit_collaboration(trees) -> CollaborationComplianceItem:
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        # auto-pairing di __init__ tanpa kriteria = implicit
        if "auto_pair" in src and "auto_collaborate" in src:
            violates = True
    return CollaborationComplianceItem(
        "COL-04", "no_implicit_collaboration", not violates,
        "collaboration is explicit (no auto-pairing)" if not violates
        else "implicit collaboration found")


def _check_deterministic(trees) -> CollaborationComplianceItem:
    nondet = ("random.", "time.time", "datetime.now", "uuid.uuid4")
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        for tok in nondet:
            if tok in src:
                violates = True
    return CollaborationComplianceItem(
        "COL-05", "deterministic", not violates,
        "no random/time in collaboration logic" if not violates
        else "non-determinism found")


def _check_registry_based(trees) -> CollaborationComplianceItem:
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if ("registry" in src) or ("CitizenRegistry" in src):
            ok = True
    return CollaborationComplianceItem(
        "COL-06", "registry_based", ok,
        "collaboration lookup via registry" if ok else "no registry usage")


def _check_compatibility_assessment(trees) -> CollaborationComplianceItem:
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "compatible" in src and "CompatibilityVerdict" in src:
            ok = True
    return CollaborationComplianceItem(
        "COL-07", "compatibility_assessment", ok,
        "compatibility is assessment (verdict)" if ok
        else "no compatibility verdict")


def _check_contract_resolution_not_execution(trees) -> CollaborationComplianceItem:
    ok = False
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "ContractResolution" in src and "resolve" in src:
            ok = True
        if "execute_contract" in src or "invoke_contract" in src or \
                "run_contract" in src:
            violates = True
    return CollaborationComplianceItem(
        "COL-08", "contract_resolution_not_execution", ok and not violates,
        "contract resolution is lookup, not execution" if ok and not violates
        else "contract execution found or resolution missing")


def _check_explainability_preserved(trees) -> CollaborationComplianceItem:
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "explain" in src and ("evidence" in src or "basis" in src or
                                 "statements" in src):
            ok = True
    return CollaborationComplianceItem(
        "COL-09", "explainability_preserved", ok,
        "explanation carries evidence/basis" if ok
        else "explainability missing")


def _check_no_mutation(trees) -> CollaborationComplianceItem:
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        for tok in ("mutate_runtime", "mutate_governance", "restart_runtime",
                    "modify_mission", "transition_lifecycle"):
            if tok in src:
                violations.append("{}: {!r}".format(path, tok))
    return CollaborationComplianceItem(
        "COL-10", "no_mutation", not violations,
        "no runtime/governance/foundation mutation" if not violations
        else "; ".join(violations[:5]))


def compliance_check(
    source_files: List[str],
    module_root: str = "",
    implementation_dirs: Optional[Tuple[str, ...]] = None,
) -> Tuple[bool, Tuple[CollaborationComplianceItem, ...]]:
    trees = _ast_trees(source_files)
    checks = (
        _check_proposal_only(trees),
        _check_no_orchestration(trees),
        _check_no_privilege(trees),
        _check_no_implicit_collaboration(trees),
        _check_deterministic(trees),
        _check_registry_based(trees),
        _check_compatibility_assessment(trees),
        _check_contract_resolution_not_execution(trees),
        _check_explainability_preserved(trees),
        _check_no_mutation(trees),
    )
    all_pass = all(c.passed for c in checks)
    return all_pass, checks
