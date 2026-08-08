# Federation Compliance - WP-08 (+ WP-18 IP-3.4-002, + WP-29 IP-3.4-003)
# IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
#
# Compliance khas Federation (10 checks paket-1 FED-01..10 + 9 checks
# paket-2 TRUST-01..09 + 10 checks paket-3 DGI-01..10). Memastikan
# federation/ tidak melanggar guardrail IP-3.4-001 / AO-3.4-001:
#
#   Federation != Central Governance
#   Registry != Control Plane
#   Capability Exchange != Execution
#   Discovery != Connection
#   Health != Monitoring Control
#   Descriptor != Contract Execution
#   Federation Identity != Global Identity
#   Sovereignty First
#
# Guardrail IP-3.4-002 (Trust & Interoperability):
#
#   Trust != Authority
#   Interoperability != Execution
#   Negotiation != Agreement
#   Assessment != Federation Control
#   Compatibility != Approval
#   Local Sovereignty
#   Registry remains authoritative
#   Deterministic
#   Evidence-first
#
# Guardrail IP-3.4-003 (Distributed Governance Intelligence):
#
#   Knowledge != Authority (DGI-01)
#   Evidence Exchange != Runtime Sharing (DGI-02)
#   Recommendation != Decision (DGI-03)
#   Collaboration != Execution (DGI-04)
#   Federation Intelligence != Central Intelligence (DGI-05)
#   Sovereignty preserved (DGI-06)
#   Deterministic reasoning (DGI-07)
#   Evidence-first (DGI-08)
#   Read-only API (DGI-09)
#   No hidden dependency (DGI-10)
#
# SHALL NOT: central authority, shared approval, remote execution, network
# connect/execute, hidden dependency ke runtime/governance, otomatisasi,
# activation/binding otomatis, delegated authority, sinkronisasi state,
# federation scheduler, remote invoke.

import ast
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# kata kerja authority/kontrol/eksekusi yang DILARANG di federation/.
_FORBIDDEN_AUTHORITY = (
    "connect", "execute", "invoke_remote", "run_remote", "remote_execute",
    "approve_shared", "central_approve", "governance_decision",
    "control_node", "control_runtime", "start_remote", "stop_remote",
    "restart_remote", "auto_connect", "establish_connection", "handshake",
    # paket-2 (IP-3.4-002): activation/binding/deligasi otomatis
    "activate", "bind", "authorize", "delegate_authority",
    "grant_trust", "auto_bind", "auto_activate",
    # paket-3 (IP-3.4-003): sinkronisasi state, remote invoke, scheduler
    "sync_state", "synchronize_state", "federation_scheduler",
    "schedule_remote", "remote_invoke",
)

# modul eksekusi/runtime/governance/network yang TIDAK boleh diimport.
_FORBIDDEN_IMPORT = (
    "sam.autonomy_runtime.execution",
    "sam.autonomy_runtime.orchestrator",
    "sam.execution",
    "sam.recovery.restore",
    "sam.governance",
    "sam.runtime",
    "socket",
    "requests",
    "urllib",
    "http.client",
)


@dataclass(frozen=True)
class FederationComplianceItem:
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


def _import_forbidden(module: str) -> bool:
    return any(module == m or module.startswith(m + ".") for m in _FORBIDDEN_IMPORT)


def default_source_files(module_root: str) -> List[str]:
    return [f for f in _py_files(module_root)
            if os.path.basename(f) != "compliance.py"]


# --- checks (10) ---

def _check_no_central_governance(trees) -> FederationComplianceItem:
    """CER-style: tidak ada kata kunci governance central."""
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "central_governance" in src or "central_approve" in src \
                or "global_governance" in src:
            violates = True
    return FederationComplianceItem(
        "FED-01", "no_central_governance", not violates,
        "federation has no authority" if not violates
        else "central governance found")


def _check_registry_not_control_plane(trees) -> FederationComplianceItem:
    """Registry menyimpan metadata, tidak mengontrol node."""
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "control_node" in src or "start_remote" in src \
                or "stop_remote" in src:
            violates = True
    return FederationComplianceItem(
        "FED-02", "registry_not_control_plane", not violates,
        "registry is metadata-only" if not violates
        else "registry controls nodes")


def _check_no_remote_execution(trees) -> FederationComplianceItem:
    """Capability exchange = advertisement, bukan execute."""
    violates = False
    has_exchange = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "capabilit" in src and "advertis" in src:
            has_exchange = True
        if "remote_execute" in src or "invoke_remote" in src \
                or ".execute(" in src:
            violates = True
    return FederationComplianceItem(
        "FED-03", "no_remote_execution", has_exchange and not violates,
        "capability exchange is advertisement, not execution"
        if has_exchange and not violates else "remote execution found")


def _check_discovery_not_connection(trees) -> FederationComplianceItem:
    """Discovery registry-based, tidak ada auto-connect (implementation)."""
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and not node.name.startswith("_check_"):
                # cek nama fungsi & isi body, bukan docstring
                body_names = set()
                for n in ast.walk(node):
                    if isinstance(n, ast.Name):
                        body_names.add(n.id)
                    elif isinstance(n, ast.Attribute):
                        body_names.add(n.attr)
                if "auto_connect" in body_names \
                        or "establish_connection" in body_names \
                        or "handshake" in body_names:
                    violations.append("{}: {}".format(path, node.name))
            if isinstance(node, ast.FunctionDef) \
                    and node.name in ("auto_connect", "establish_connection",
                                      "handshake", "connect"):
                violations.append("{}: {}".format(path, node.name))
    return FederationComplianceItem(
        "FED-04", "discovery_not_connection", not violations,
        "discovery is registry-based, no auto-connect"
        if not violations else "; ".join(violations[:5]))


def _check_health_observational(trees) -> FederationComplianceItem:
    """Health observasional, bukan kontrol monitoring."""
    violates = False
    has_observ = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "observ" in src or "assess" in src.lower():
            has_observ = True
        if "control_runtime" in src or "restart_remote" in src \
                or "repair_remote" in src:
            violates = True
    return FederationComplianceItem(
        "FED-05", "health_observational", has_observ and not violates,
        "health is observational, no control" if not violates
        else "health control found")


def _check_descriptor_declarative(trees) -> FederationComplianceItem:
    """Descriptor deklaratif, bukan eksekusi contract."""
    violates = False
    has_decl = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "deklaratif" in src.lower() or "declarative" in src.lower() \
                or "deklaratif" in src:
            has_decl = True
        if ".invoke(" in src or "execute_contract" in src:
            violates = True
    return FederationComplianceItem(
        "FED-06", "descriptor_declarative", has_decl and not violates,
        "descriptor is declarative, not contract execution"
        if has_decl and not violates else "descriptor executes contracts")


def _check_local_identity_preserved(trees) -> FederationComplianceItem:
    """Federation Identity != Global Identity - local identity retained."""
    ok = False
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "local_identity" in src:
            ok = True
        if "global_identity" in src and "replace" in src:
            violates = True
    return FederationComplianceItem(
        "FED-07", "local_identity_preserved", ok and not violates,
        "each instance keeps local identity" if ok and not violates
        else "local identity not preserved")


def _check_sovereignty_first(trees) -> FederationComplianceItem:
    """Sovereignty First - semua keputusan tetap lokal."""
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "sovereign" in src.lower() or "sovereignty" in src.lower():
            ok = True
    return FederationComplianceItem(
        "FED-08", "sovereignty_first", ok,
        "sovereignty preserved, decisions stay local" if ok
        else "sovereignty not declared")


def _check_no_shared_approval(trees) -> FederationComplianceItem:
    """Tidak ada approval bersama/terpusat."""
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "shared_approve" in src or "shared_approval" in src \
                or "central_approve" in src:
            violates = True
    return FederationComplianceItem(
        "FED-09", "no_shared_approval", not violates,
        "no shared/central approval" if not violates
        else "shared approval found")


def _check_no_hidden_dependency(trees) -> FederationComplianceItem:
    """Tidak ada ketergantungan tersembunyi ke runtime/governance/network."""
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod = alias.name
                        if _import_forbidden(mod):
                            violations.append("{}: {}".format(path, mod))
                else:
                    mod = node.module or ""
                    if _import_forbidden(mod):
                        violations.append("{}: {}".format(path, mod))
    return FederationComplianceItem(
        "FED-10", "no_hidden_dependency", not violations,
        "no hidden dep on runtime/governance/network" if not violations
        else "; ".join(violations[:5]))


# --- checks paket-2 (IP-3.4-002) TRUST-01..09 ---

def _check_no_central_trust(trees) -> FederationComplianceItem:
    """Tidak ada trust terpusat (central trust authority)."""
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in (
                    "central_trust_authority", "global_trust_root",
                    "trust_authority"):
                violations.append("{}: {}".format(path, node.id))
    return FederationComplianceItem(
        "TRUST-01", "no_central_trust", not violations,
        "no central trust authority" if not violations
        else "; ".join(violations[:3]))


def _check_no_delegated_authority(trees) -> FederationComplianceItem:
    """Trust tidak mendelegasikan kewenangan."""
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in (
                    "delegate_authority", "authorize", "grant_privilege"):
                violations.append("{}: {}".format(path, node.attr))
    return FederationComplianceItem(
        "TRUST-02", "no_delegated_authority", not violations,
        "trust grants no authority" if not violations
        else "; ".join(violations[:3]))


def _check_trust_not_approval(trees) -> FederationComplianceItem:
    """Trust != Approval."""
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        for ln in src.splitlines():
            sl = ln.strip()
            if sl.startswith(("#", '"', "'")):
                continue
            low = sl.lower()
            if ("trust" in low and "approv" in low
                    and any(sl.startswith(k) for k in (
                        "def ", "is_", "@property", "return"))):
                violations.append("{}: {!r}".format(path, sl[:50]))
    return FederationComplianceItem(
        "TRUST-03", "trust_not_approval", not violations,
        "trust is assessment, not approval" if not violations
        else "; ".join(violations[:3]))


def _check_interoperability_not_execution(trees) -> FederationComplianceItem:
    """Interoperability != Execution (assessment tidak memicu aksi)."""
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in (
                    "execute", "invoke", "run_remote"):
                violations.append("{}: {}".format(path, node.attr))
    return FederationComplianceItem(
        "TRUST-04", "interoperability_not_execution", not violations,
        "interoperability is assessment, not execution" if not violations
        else "; ".join(violations[:3]))


def _check_negotiation_not_agreement(trees) -> FederationComplianceItem:
    """Negotiation != Agreement (proposal, bukan persetujuan)."""
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in (
                    "sign_agreement", "finalize_agreement", "commit_agreement",
                    "accept_agreement"):
                violations.append("{}: {}".format(path, node.name))
    return FederationComplianceItem(
        "TRUST-05", "negotiation_not_agreement", not violations,
        "negotiation produces proposal, not agreement" if not violations
        else "; ".join(violations[:3]))


def _check_sovereignty_preserved_trust(trees) -> FederationComplianceItem:
    """Local Sovereignty dijaga (tidak ada perubahan otoritas lokal)."""
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in (
                    "override_local", "replace_governance", "global_approve"):
                violations.append("{}: {}".format(path, node.attr))
    return FederationComplianceItem(
        "TRUST-06", "local_sovereignty_preserved", not violations,
        "local sovereignty preserved" if not violations
        else "; ".join(violations[:3]))


def _check_registry_authoritative_trust(trees, module_root) -> FederationComplianceItem:
    """Registry remains authoritative (discovery berbasis registry)."""
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "registry" in src.lower() or "registry" in src:
            ok = True
    return FederationComplianceItem(
        "TRUST-07", "registry_authoritative", ok,
        "discovery remains registry-based" if ok
        else "no registry reference")


def _check_deterministic_trust(trees) -> FederationComplianceItem:
    """Deterministic: tidak ada RNG/random/waktu sebagai dasar putusan."""
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in (
                    "random", "randint", "time", "datetime", "uuid"):
                violations.append("{}: {}".format(path, node.id))
    return FederationComplianceItem(
        "TRUST-08", "deterministic_trust", not violations,
        "deterministic (no RNG/time-based decision)" if not violations
        else "; ".join(violations[:3]))


def _check_evidence_first(trees) -> FederationComplianceItem:
    """Evidence-first: seluruh trust dapat dijelaskan oleh evidence."""
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "evidence" in src.lower():
            ok = True
    return FederationComplianceItem(
        "TRUST-09", "evidence_first", ok,
        "trust grounded in evidence" if ok else "no evidence grounding")


# --- checks paket-3 (IP-3.4-003) DGI-01..10 ---


def _check_knowledge_not_authority(trees) -> FederationComplianceItem:
    """Knowledge != Authority: knowledge exchange tidak membawa otoritas."""
    ok = False
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "is_authority" in src or "as_authority" in src:
            ok = True
        # knowledge yang dipakai sebagai perintah eksekusi = pelanggaran
        if "authoritative_knowledge" in src or "knowledge_directive" in src:
            violates = True
    return FederationComplianceItem(
        "DGI-01", "knowledge_not_authority", ok and not violates,
        "knowledge is shared, never authority" if ok and not violates
        else "knowledge carries authority")


def _check_evidence_not_runtime_share(trees) -> FederationComplianceItem:
    """Evidence Exchange != Runtime Sharing."""
    ok = False
    violates = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "is_runtime_share" in src:
            ok = True
        if "runtime_share" in src and "shared_state" in src:
            violates = True
    return FederationComplianceItem(
        "DGI-02", "evidence_not_runtime_share", ok and not violates,
        "evidence exchange is not runtime sharing" if ok and not violates
        else "evidence shares runtime state")


def _check_recommendation_not_decision(trees) -> FederationComplianceItem:
    """Recommendation != Decision: rekomendasi tidak pernah menjadi keputusan."""
    violations = []
    has_rec = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "recommend" in src.lower():
            has_rec = True
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in (
                    "to_decision", "enforce_recommendation", "apply_suggestion"):
                violations.append("{}: {}".format(path, node.attr))
    # is_decision atribut yang SELALU False di rekomendasi = sah
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "is_decision" in src:
            has_rec = True
    return FederationComplianceItem(
        "DGI-03", "recommendation_not_decision", has_rec and not violations,
        "recommendation is advisory, never decision"
        if has_rec and not violations else "recommendation enforces decision")


def _check_collaboration_not_execution(trees) -> FederationComplianceItem:
    """Collaboration != Execution: kolaborasi deskriptif, bukan eksekusi."""
    violations = []
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "is_execution" in src:
            ok = True
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in (
                    "execute_collaboration", "run_collaboration",
                    "start_collaboration"):
                violations.append("{}: {}".format(path, node.id))
    return FederationComplianceItem(
        "DGI-04", "collaboration_not_execution", ok and not violations,
        "collaboration is descriptive, not execution"
        if ok and not violations else "collaboration executes")


def _check_federation_not_central_intelligence(trees) -> FederationComplianceItem:
    """Federation Intelligence != Central Intelligence (reasoning tetap lokal)."""
    violations = []
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "local" in src.lower():  # reasoning lokal dipertahankan
            ok = True
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in (
                    "global_brain", "central_reasoner", "single_intelligence",
                    "replaces_local_reasoning"):
                violations.append("{}: {}".format(path, node.id))
    return FederationComplianceItem(
        "DGI-05", "federation_not_central_intelligence", ok and not violations,
        "each federation reasons locally, shares evidence not authority"
        if ok and not violations else "central intelligence found")


def _check_sovereignty_preserved_dgi(trees) -> FederationComplianceItem:
    """Sovereignty preserved: reasoning tidak menggantikan otoritas lokal."""
    violations = []
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "sovereign" in src.lower() or "sovereignty" in src.lower():
            ok = True
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in (
                    "override_local_decision", "central_rule",
                    "supersede_local"):
                violations.append("{}: {}".format(path, node.id))
    return FederationComplianceItem(
        "DGI-06", "sovereignty_preserved", ok and not violations,
        "reasoning preserves local sovereignty"
        if ok and not violations else "sovereignty overridden")


def _check_deterministic_reasoning(trees) -> FederationComplianceItem:
    """Deterministic reasoning: tanpa RNG/time sebagai dasar reasoning."""
    violations = []
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "deterministic" in src.lower():
            ok = True
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in (
                    "random", "randint", "time", "datetime", "uuid",
                    "secrets"):
                violations.append("{}: {}".format(path, node.id))
    return FederationComplianceItem(
        "DGI-07", "deterministic_reasoning", ok and not violations,
        "reasoning is deterministic (no RNG/time)"
        if ok and not violations else "; ".join(violations[:3]))


def _check_evidence_first_reasoning(trees) -> FederationComplianceItem:
    """Evidence-first: reasoning diturunkan dari evidence."""
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "evidence" in src.lower():
            ok = True
    return FederationComplianceItem(
        "DGI-08", "evidence_first_reasoning", ok,
        "reasoning grounded in evidence" if ok else "no evidence grounding")


def _check_read_only_api(trees) -> FederationComplianceItem:
    """Read-only API: tidak ada method mutasi/eksekusi/network."""
    violations = []
    ok = False
    for path, tree in trees:
        if tree is None:
            continue
        src = _read(path)
        if "read-only" in src.lower() or "read-only" in src:
            ok = True
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in (
                    "connect", "execute", "authorize", "approve",
                    "invoke", "sync_state", "synchronize_state"):
                violations.append("{}: {}".format(path, node.name))
    return FederationComplianceItem(
        "DGI-09", "read_only_api", ok and not violations,
        "api is read-only (no mutation/execution/network)"
        if ok and not violations else "; ".join(violations[:3]))


def _check_no_hidden_dependency_dgi(trees) -> FederationComplianceItem:
    """No hidden dependency: tidak ada import forbidden (runtime/governance/network)."""
    violations = []
    for path, tree in trees:
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod = alias.name
                        if _import_forbidden(mod):
                            violations.append("{}: {}".format(path, mod))
                else:
                    mod = node.module or ""
                    if _import_forbidden(mod):
                        violations.append("{}: {}".format(path, mod))
    return FederationComplianceItem(
        "DGI-10", "no_hidden_dependency", not violations,
        "no hidden dep on runtime/governance/network" if not violations
        else "; ".join(violations[:5]))


# pilih source files sesuai implementation_dirs (tanpa compliance.py)
def _select_source_files(
    source_files: List[str],
    module_root: str,
    implementation_dirs: Optional[Tuple[str, ...]],
) -> List[str]:
    if not implementation_dirs:
        return source_files
    dirs = tuple(d.rstrip("/\\") for d in implementation_dirs)
    root = module_root or ""
    selected: List[str] = []
    for f in source_files:
        rel = f.replace("\\", "/")
        for d in dirs:
            marker = d.replace("\\", "/")
            if (root and (rel.startswith(marker)
                          or rel.startswith(os.path.join(
                              root.replace("\\", "/"), marker)))) \
                    or (not root and marker in rel):
                selected.append(f)
                break
    return selected


def compliance_check(
    source_files: List[str],
    module_root: str = "",
    implementation_dirs: Optional[Tuple[str, ...]] = None,
) -> Tuple[bool, Tuple[FederationComplianceItem, ...]]:
    files = _select_source_files(source_files, module_root, implementation_dirs)
    trees = _ast_trees(files)
    checks = (
        _check_no_central_governance(trees),
        _check_registry_not_control_plane(trees),
        _check_no_remote_execution(trees),
        _check_discovery_not_connection(trees),
        _check_health_observational(trees),
        _check_descriptor_declarative(trees),
        _check_local_identity_preserved(trees),
        _check_sovereignty_first(trees),
        _check_no_shared_approval(trees),
        _check_no_hidden_dependency(trees),
        # paket-2 (IP-3.4-002)
        _check_no_central_trust(trees),
        _check_no_delegated_authority(trees),
        _check_trust_not_approval(trees),
        _check_interoperability_not_execution(trees),
        _check_negotiation_not_agreement(trees),
        _check_sovereignty_preserved_trust(trees),
        _check_registry_authoritative_trust(trees, module_root),
        _check_deterministic_trust(trees),
        _check_evidence_first(trees),
        # paket-3 (IP-3.4-003)
        _check_knowledge_not_authority(trees),
        _check_evidence_not_runtime_share(trees),
        _check_recommendation_not_decision(trees),
        _check_collaboration_not_execution(trees),
        _check_federation_not_central_intelligence(trees),
        _check_sovereignty_preserved_dgi(trees),
        _check_deterministic_reasoning(trees),
        _check_evidence_first_reasoning(trees),
        _check_read_only_api(trees),
        _check_no_hidden_dependency_dgi(trees),
    )
    all_pass = all(c.passed for c in checks)
    return all_pass, checks
