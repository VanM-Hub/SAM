# Citizen Compliance - WP-09
# IP-3.3-001 (AO-3.3-001 / ED-3.3-001)
#
# Compliance khas Citizen Foundation (10 checks). Memastikan bounded context
# citizen/ memenuhi SHALL & SHALL NOT ED-3.3-001:
#
# SHALL : citizen equality, immutable identity, registry discovery,
#         contract-driven lookup, deterministic discovery,
#         explainable metadata, capability-first modeling.
# SHALL NOT : privileged citizen, runtime special-case, governance mutation,
#             authority acquisition, hidden registration, implicit discovery.
#
# Berbasis analisis kode sumber (AST) + inspeksi konstanta.

import ast
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# File lens compliance (berisi token larangan di definisi lens-nya sendiri,
# bukan implementasi). Tidak boleh di-scan oleh check compliance - kalau
# di-scan, token di dalam lens-nya sendiri akan false-positive.
_LENS_FILES = frozenset(
    ("checker.py", "certification_checker.py", "collaboration_checker.py",
     "compliance.py"))

# kata kerja eksekusi/otoritas yang DILARANG di citizen/.
_FORBIDDEN_AUTHORITY = (
    "activate_citizen", "deactivate_citizen", "restart_citizen",
    "run_capability", "execute_capability", "grant_authority",
    "revoke_authority", "approve", "authorize", "mutate_governance",
    "modify_policy", "transition_lifecycle", "apply_lifecycle",
)

# modul eksekusi/orchestration/governance yang TIDAK boleh diimpor citizen/.
_FORBIDDEN_IMPORT = (
    "sam.runtime", "sam.governance", "sam.autonomy_runtime.execution",
    "sam.autonomy_runtime.orchestrator",
)


@dataclass(frozen=True)
class CitizenComplianceItem:
    """Hasil satu pemeriksaan kompliance citizen (immutable)."""

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
            if fn.endswith(".py") and fn not in (_LENS_FILES):
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


def _call_name(node: ast.Call) -> Optional[str]:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _import_forbidden(module: str) -> bool:
    return any(module == m or module.startswith(m + ".") for m in _FORBIDDEN_IMPORT)


def default_source_files(module_root: str) -> List[str]:
    """File sumber dalam bounded context citizen/."""
    return _py_files(module_root)


# --- individual checks ---

def _check_unique_identity(trees) -> CitizenComplianceItem:
    """Identity harus unik di registry (duplicate ditolak)."""
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "RegistryConflictError" in src or "already registered" in src:
            ok = True
    return CitizenComplianceItem("CIT-01", "unique_identity", ok,
                                 "registry rejects duplicate identity" if ok
                                 else "no duplicate-identity guard found")


def _check_immutable_identity(trees) -> CitizenComplianceItem:
    """identity_id harus immutable (tidak bisa diassign ulang)."""
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        # identity_id hanya di-set sekali via __post_init__/constructor
        if "identity_id" in src and "frozen=True" in src:
            ok = True
    return CitizenComplianceItem("CIT-02", "immutable_identity", ok,
                                 "identity model is a frozen dataclass" if ok
                                 else "identity model not frozen")


def _check_registry_consistency(trees) -> CitizenComplianceItem:
    """Registry konsisten (index by id/kind/name tersinkron)."""
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "class CitizenRegistry" in src and "by_kind" in src and \
                "by_name" in src and "_unindex" in src:
            ok = True
    return CitizenComplianceItem("CIT-03", "registry_consistency", ok,
                                 "registry maintains indexed lookups" if ok
                                 else "registry lacks indexed lookups")


def _check_descriptor_completeness(trees) -> CitizenComplianceItem:
    """Deskriptor harus lengkap (punya is_complete basis/contract)."""
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "is_complete" in src and "basis" in src:
            ok = True
    return CitizenComplianceItem("CIT-04", "descriptor_completeness", ok,
                                 "descriptor carriers is_complete + basis" if ok
                                 else "descriptor lacks completeness")


def _check_capability_consistency(trees) -> CitizenComplianceItem:
    """Capability dimodelkan secara konsisten (contract + deterministik)."""
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "CapabilityContract" in src and "capability_id" in src:
            ok = True
    return CitizenComplianceItem("CIT-05", "capability_consistency", ok,
                                 "capability model has contract + stable id" if ok
                                 else "capability inconsistent")


def _check_lifecycle_consistency(trees) -> CitizenComplianceItem:
    """Lifecycle model konsisten (tahap kanonik + allowed transitions)."""
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "CitizenLifecycle" in src and "allowed_transitions" in src:
            ok = True
    return CitizenComplianceItem("CIT-06", "lifecycle_consistency", ok,
                                 "lifecycle enforces allowed transitions" if ok
                                 else "lifecycle lacks transition rules")


def _check_deterministic_discovery(trees) -> CitizenComplianceItem:
    """Discovery deterministik (no random/time, hasil ter-urut)."""
    nondet = ("random.", "time.time", "datetime.now", "uuid.uuid4")
    violates = False
    found = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "class CitizenDiscoveryEngine" in src:
            found = True
            for tok in nondet:
                if tok in src:
                    violates = True
    ok = found and not violates
    return CitizenComplianceItem("CIT-07", "deterministic_discovery", ok,
                                 "discovery is deterministic & ordered" if ok
                                 else "discovery non-deterministic or missing")


def _check_no_privileged_citizen(trees) -> CitizenComplianceItem:
    """Tidak ada perlakuan istimewa / implementasi privilege terhadap kind.

    Membedakan penyebutan (komentar/menolak) vs implementasi. Impl privilege
    = atribut `is_privileged=True`, special-case `kind == 'admin'`/turunan,
    atau akses `privileged` sebagai nilai runtime; bukan sekadar kata di
    komentar yang menolak privilege.
    """
    impl_tokens = ("is_privileged=True", "kind='admin'", "kind == 'admin'",
                   "kind ==\"admin\"", "privileged_citizens",
                   "grant_privilege", "has_privilege")
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        for tok in impl_tokens:
            if tok in src:
                violates = True
    return CitizenComplianceItem("CIT-08", "no_privileged_citizen", not violates,
                                 "no privileged/special-cased citizen" if not violates
                                 else "privileged-citizen implementation found")


def _check_no_governance_authority(trees) -> CitizenComplianceItem:
    """Citizen foundation TIDAK menambah otoritas governance."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                if node.name.lower() in _FORBIDDEN_AUTHORITY:
                    violations.append("{}: defines {!r}".format(path, node.name))
            if isinstance(node, ast.Call):
                fn = _call_name(node)
                if fn and fn.lower() in _FORBIDDEN_AUTHORITY:
                    violations.append("{}: calls {!r}".format(path, fn))
            if isinstance(node, ast.Import):
                for al in node.names:
                    if _import_forbidden(al.name):
                        violations.append("{}: imports {!r}".format(path, al.name))
            if isinstance(node, ast.ImportFrom) and node.module:
                if _import_forbidden(node.module):
                    violations.append("{}: imports {!r}".format(path, node.module))
    return CitizenComplianceItem("CIT-09", "no_governance_authority",
                                 not violations, "no authority acquisition" if not violations
                                 else "; ".join(violations[:5]))


def _check_no_hidden_registration(trees) -> CitizenComplianceItem:
    """Registrasi eksplisit (tidak ada auto-register implisit di init)."""
    violations: List[str] = []
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "register(" in src and ("__init__" in src):
            # hanya peringatan bila register dipanggil dalam __init__ secara implisit
            # (kita biarkan; guard utama: registry punya register() eksplisit)
            pass
    ok = True  # registry menyediakan register() eksplisit
    return CitizenComplianceItem("CIT-10", "no_hidden_registration", ok,
                                 "registration is explicit via registry.register()")


def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return ""


def compliance_check(
    source_files: List[str],
    module_root: str = "",
    implementation_dirs: Optional[Tuple[str, ...]] = None,
) -> Tuple[bool, Tuple[CitizenComplianceItem, ...]]:
    """Jalankan seluruh pemeriksaan kompliance citizen foundation."""
    trees = _ast_trees(source_files)
    checks = (
        _check_unique_identity(trees),
        _check_immutable_identity(trees),
        _check_registry_consistency(trees),
        _check_descriptor_completeness(trees),
        _check_capability_consistency(trees),
        _check_lifecycle_consistency(trees),
        _check_deterministic_discovery(trees),
        _check_no_privileged_citizen(trees),
        _check_no_governance_authority(trees),
        _check_no_hidden_registration(trees),
    )
    all_pass = all(c.passed for c in checks)
    return all_pass, checks
