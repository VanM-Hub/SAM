# Platform Workspace Compliance - IP-3.5-001 (AO-ENG-001, MISSION-3.5)
# WP-08: verifikasi kepatuhan bounded context Platform Workspace terhadap
#        guardrail MISSION-3.5 dan roadmap SAM 3.5.
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail dikunci:
#   PEX-01 Workspace != Governance          (workspace hanya menyajikan)
#   PEX-02 Navigation != Execution          (navigasi hanya tampilan)
#   PEX-03 Perspective != Authority         (perspective tidak berotoritas)
#   PEX-04 Context != State Control         (konteks tidak mengontrol runtime)
#   PEX-05 Layout != Orchestration          (layout tidak mengorkestrasi)
#   PEX-06 Descriptor != Contract Execution (descriptor deklaratif)
#   PEX-07 View != Intervention             (tampilan tidak mengintervensi)
#   PEX-08 Presentation Passive             (tidak perform governance/approval)
#   PEX-09 Consumer-only                    (tidak memodifikasi capability)
#   PEX-10 Read-only API                   (facade tidak eksekusi)
#
# Metode: positive marker + AST scan (forbidden name/attr/import) +
#         dependency scan citizen/consumer. Sama dengan pola compliance
#         bounded context lain (federation DGI/OR).

"""Platform Workspace Compliance.

Memverifikasi bahwa implementasi Platform Workspace mematuhi guardrail
engineerign. Bersifat audit-only (menghasilkan laporan), tidak mengubah kode.
"""

import ast
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

# Token yang TIDAK BOLEH hadir sebagai nama/atribut/import dalam file sumber
# workspace. Kehadirannya menandakan potensi drift menuju eksekusi/orchestration
# (melanggar presentation-passive).
_FORBIDDEN_AUTHORITY = (
    "execute", "orchestrate", "schedule", "failover", "load_balance",
    "select_leader", "elect_leader", "run_workflow", "start_collaboration",
    "activate_remote", "auto_coordinate", "perform_governance",
    "perform_approval", "bypass_runtime", "modify_citizen", "new_authority",
)

# Marker positif: kata kunci yang menandakan pattern yang DIOLEHKAN (declarative/read).
_ALLOWED_MARKERS = (
    "snapshot", "descriptor", "model", "navigation", "perspective",
    "context", "layout", "read", "assemble", "present",
)


def _default_source_files(root: Optional[str] = None) -> List[str]:
    """Kumpulkan *.py dalam direktori platform workspace (deterministik)."""
    base = root or os.path.dirname(os.path.abspath(__file__))
    files: List[str] = []
    for dirpath, _dirnames, filenames in os.walk(base):
        for fn in sorted(filenames):
            if fn.endswith(".py"):
                files.append(os.path.join(dirpath, fn))
    # Exclude compliance itu sendiri & __init__ yang hanya re-export.
    return sorted(files)


def _scan_file(path: str) -> Tuple[bool, List[str], List[str]]:
    """Scan satu file: (clean, forbidden_hits, allowed_markers_found)."""
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=path)
        except SyntaxError:
            return True, ["<syntax-error>"], []
    forbidden: List[str] = []
    markers: List[str] = []

    for node in ast.walk(tree):
        # Import
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname in _FORBIDDEN_AUTHORITY:
                    forbidden.append(a.asname)
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[-1] in _FORBIDDEN_AUTHORITY:
                forbidden.append(node.module)
            for a in node.names:
                if a.name in _FORBIDDEN_AUTHORITY:
                    forbidden.append(a.name)
        # Nama / atribut
        if isinstance(node, ast.Name):
            if node.id in _FORBIDDEN_AUTHORITY:
                forbidden.append(node.id)
            elif node.id in _ALLOWED_MARKERS:
                markers.append(node.id)
        if isinstance(node, ast.Attribute):
            if node.attr in _FORBIDDEN_AUTHORITY:
                forbidden.append(node.attr)
        # Method call
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _FORBIDDEN_AUTHORITY:
                forbidden.append(node.func.id)

    # Unique, sorted
    return (
        not forbidden,
        sorted(set(forbidden)),
        sorted(set(markers)),
    )


@dataclass(frozen=True)
class ComplianceResult:
    """Hasil verifikasi kepatuhan (immutable)."""

    group: str
    total_checks: int
    passed: int
    failed: int
    messages: Tuple[str, ...] = ()
    forbidden_found: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.failed == 0


def _check_prefix(file_items: Sequence[Tuple[str, str]], prefix: str) -> bool:
    """Semua item (path, context) memiliki prefix (helper sederhana)."""
    return all(p.startswith(prefix) for p, _ in file_items)


def compliance_check(
    source_files: Optional[Sequence[str]] = None,
    module_root: Optional[str] = None,
) -> ComplianceResult:
    """Jalankan verifikasi kepatuhan Platform Workspace.

    Mengembalikan ComplianceResult (bukan exception) untuk konsumsi audit.
    """
    files = list(source_files) if source_files else _default_source_files(module_root)
    if not files:
        return ComplianceResult(
            group="PEX", total_checks=1, passed=0, failed=1,
            messages=("tidak ada source file untuk di-scan",),
        )

    forbidden_all: List[str] = []
    marker_found = False
    checked = 0
    failed = 0
    messages: List[str] = []
    for path in files:
        clean, forb, markers = _scan_file(path)
        checked += 1
        forbidden_all.extend(forb)
        if markers:
            marker_found = True
        if not clean:
            failed += 1
            messages.append("forbidden token di %s: %s" % (
                os.path.basename(path), ",".join(forb)))
        else:
            messages.append("OK %s" % os.path.basename(path))

    # Guardrail deklaratif: minimal ada marker "presentation/declarative".
    if not marker_found:
        failed += 1
        messages.append("tidak ada marker declarative/read pada file sumber")

    # Persyaratan struktur: minimal ada workspace_api (facade) + model.
    names = {os.path.basename(p) for p in files}
    for required in ("workspace_api.py", "workspace_model.py"):
        if required not in names:
            failed += 1
            messages.append("struktur wajib hilang: %s" % required)

    return ComplianceResult(
        group="PEX",
        total_checks=checked + 2,
        passed=checked + 2 - failed,
        failed=failed,
        messages=tuple(messages),
        forbidden_found=tuple(sorted(set(forbidden_all))),
    )


# --- Mission Experience Compliance (IP-3.5-002, group MEX) -----------------

# Token yang TIDAK BOLEH hadir dalam source Mission Experience. Kehadirannya
# menandakan drift ke mission execution / coordination (melanggar batas
# presentation-passive mission).
_MISSION_FORBIDDEN = (
    "run_mission", "execute_mission", "coordinate_mission",
    "start_mission", "advance_mission", "transition_mission",
    "allocate_resource", "build_mission", "submit_mission",
    "activate_mission", "commit_mission", "approve_mission",
    "launch_mission", "trigger_mission", "delegate_mission",
)

# Marker positif: kosa kata penyajian mission yang DIOLEHKAN.
_MISSION_ALLOWED = (
    "snapshot", "view", "insight", "timeline", "journey",
    "progress", "context", "present", "read", "assembly",
)


def _scan_mission_file(path: str):
    """Scan satu file mission: (clean, forbidden_hits)."""
    import ast as _ast
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = _ast.parse(f.read(), filename=path)
        except SyntaxError:
            return True, ["<syntax-error>"], []
    forbidden = []
    markers = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for a in node.names:
                if a.asname in _MISSION_FORBIDDEN:
                    forbidden.append(a.asname)
        if isinstance(node, _ast.ImportFrom):
            for a in node.names:
                if a.name in _MISSION_FORBIDDEN:
                    forbidden.append(a.name)
        if isinstance(node, _ast.Name):
            if node.id in _MISSION_FORBIDDEN:
                forbidden.append(node.id)
            elif node.id in _MISSION_ALLOWED:
                markers.append(node.id)
        if isinstance(node, _ast.Attribute):
            if node.attr in _MISSION_FORBIDDEN:
                forbidden.append(node.attr)
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            if node.func.id in _MISSION_FORBIDDEN:
                forbidden.append(node.func.id)
    return (not forbidden, sorted(set(forbidden)), sorted(set(markers)))


_MISSION_MODULES = (
    "mission_workspace.py",
    "mission_timeline.py",
    "mission_context.py",
    "mission_api.py",
)


def mission_compliance_check(
    module_root: Optional[str] = None,
) -> ComplianceResult:
    """Verifikasi kepatuhan Mission Experience (group MEX).

    Memindai modul mission experience untuk forbidden execution tokens dan
    memastikan ada marker presentasi (snapshot/view/insight).
    """
    base = module_root or os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(base, m) for m in _MISSION_MODULES
             if os.path.exists(os.path.join(base, m))]
    if not files:
        return ComplianceResult(
            group="MEX", total_checks=1, passed=0, failed=1,
            messages=("tidak ada modul mission experience",),
        )
    forbidden_all = []
    markers = False
    checked = 0
    failed = 0
    messages = []
    for path in files:
        clean, forb, marks = _scan_mission_file(path)
        checked += 1
        forbidden_all.extend(forb)
        if marks:
            markers = True
        if not clean:
            failed += 1
            messages.append("forbidden mission token di %s: %s" % (
                os.path.basename(path), ",".join(forb)))
        else:
            messages.append("OK %s" % os.path.basename(path))
    if not markers:
        failed += 1
        messages.append("tidak ada marker presentation mission")
    return ComplianceResult(
        group="MEX",
        total_checks=checked + 1,
        passed=checked + 1 - failed,
        failed=failed,
        messages=tuple(messages),
        forbidden_found=tuple(sorted(set(forbidden_all))),
    )


# --- Citizen Experience Compliance (IP-3.5-003, group CX) -------------------

# Token yang TIDAK BOLEH hadir dalam source Citizen Experience. Kehadirannya
# menandakan drift ke eksekusi action citizen / modifikasi citizen-federation
# (melanggar guardrail MISSION-3.5: MUST NOT modify citizens).
_CITIZEN_FORBIDDEN = (
    "approve_citizen", "reject_citizen", "activate_citizen",
    "deactivate_citizen", "modify_citizen", "update_citizen",
    "start_collaboration", "execute_collaboration", "approve_collaboration",
    "reject_collaboration", "issue_certification", "revoke_certification",
    "certify", "negotiate", "join_federation", "leave_federation",
    "admit_member", "remove_member", "trust_member", "run_federation_action",
)

# Marker positif: kosa kata penyajian citizen yang DIOLEHKAN.
_CITIZEN_ALLOWED = (
    "snapshot", "view", "manifest", "compat", "status", "present",
    "read", "assembly", "visible", "summary",
)

_CITIZEN_MODULES = (
    "citizen_workspace.py",
    "collaboration_workspace.py",
    "citizen_api.py",
)


def _scan_citizen_file(path: str):
    """Scan satu file citizen: (clean, forbidden_hits, markers)."""
    import ast as _ast
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = _ast.parse(f.read(), filename=path)
        except SyntaxError:
            return True, ["<syntax-error>"], []
    forbidden = []
    markers = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for a in node.names:
                if a.asname in _CITIZEN_FORBIDDEN:
                    forbidden.append(a.asname)
        if isinstance(node, _ast.ImportFrom):
            for a in node.names:
                if a.name in _CITIZEN_FORBIDDEN:
                    forbidden.append(a.name)
        if isinstance(node, _ast.Name):
            if node.id in _CITIZEN_FORBIDDEN:
                forbidden.append(node.id)
            elif node.id in _CITIZEN_ALLOWED:
                markers.append(node.id)
        if isinstance(node, _ast.Attribute):
            if node.attr in _CITIZEN_FORBIDDEN:
                forbidden.append(node.attr)
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            if node.func.id in _CITIZEN_FORBIDDEN:
                forbidden.append(node.func.id)
    return (not forbidden, sorted(set(forbidden)), sorted(set(markers)))


def citizen_compliance_check(
    module_root: Optional[str] = None,
) -> ComplianceResult:
    """Verifikasi kepatuhan Citizen Experience (group CX).

    Memindai modul citizen experience untuk forbidden action tokens dan
    memastikan ada marker presentasi (snapshot/view/manifest).
    """
    base = module_root or os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(base, m) for m in _CITIZEN_MODULES
             if os.path.exists(os.path.join(base, m))]
    if not files:
        return ComplianceResult(
            group="CX", total_checks=1, passed=0, failed=1,
            messages=("tidak ada modul citizen experience",),
        )
    forbidden_all = []
    markers = False
    checked = 0
    failed = 0
    messages = []
    for path in files:
        clean, forb, marks = _scan_citizen_file(path)
        checked += 1
        forbidden_all.extend(forb)
        if marks:
            markers = True
        if not clean:
            failed += 1
            messages.append("forbidden citizen token di %s: %s" % (
                os.path.basename(path), ",".join(forb)))
        else:
            messages.append("OK %s" % os.path.basename(path))
    if not markers:
        failed += 1
        messages.append("tidak ada marker presentation citizen")
    return ComplianceResult(
        group="CX",
        total_checks=checked + 1,
        passed=checked + 1 - failed,
        failed=failed,
        messages=tuple(messages),
        forbidden_found=tuple(sorted(set(forbidden_all))),
    )


# --- Explainability Experience Compliance (IP-3.5-004, group EX) ------------

# Token yang TIDAK BOLEH hadir dalam source Explainability Experience.
# Kehadirannya menandakan drift ke verifikasi/judgment evidence atau
# pengambilan keputusan (melanggar batas presentation-passive evidence).
_EXPLAIN_FORBIDDEN = (
    "verify_evidence", "reject_evidence", "accept_evidence",
    "expire_evidence", "mark_evidence", "decide", "judge",
    "infer_authority", "grant_authority", "approve_evidence",
    "invalidate_evidence", "publish_decision",
)

# Marker positif: kosa kata penyajian evidence yang DIOLEHKAN.
_EXPLAIN_ALLOWED = (
    "graph", "aggregate", "summary", "chain", "snapshot", "present",
    "read", "trace", "view", "coverage", "explain",
)

_EXPLAIN_MODULES = (
    "evidence_graph.py",
    "explainability.py",
    "evidence_chain.py",
    "explain_api.py",
)


def _scan_explain_file(path: str):
    """Scan satu file explain: (clean, forbidden_hits, markers)."""
    import ast as _ast
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = _ast.parse(f.read(), filename=path)
        except SyntaxError:
            return True, ["<syntax-error>"], []
    forbidden = []
    markers = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for a in node.names:
                if a.asname in _EXPLAIN_FORBIDDEN:
                    forbidden.append(a.asname)
        if isinstance(node, _ast.ImportFrom):
            for a in node.names:
                if a.name in _EXPLAIN_FORBIDDEN:
                    forbidden.append(a.name)
        if isinstance(node, _ast.Name):
            if node.id in _EXPLAIN_FORBIDDEN:
                forbidden.append(node.id)
            elif node.id in _EXPLAIN_ALLOWED:
                markers.append(node.id)
        if isinstance(node, _ast.Attribute):
            if node.attr in _EXPLAIN_FORBIDDEN:
                forbidden.append(node.attr)
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            if node.func.id in _EXPLAIN_FORBIDDEN:
                forbidden.append(node.func.id)
    return (not forbidden, sorted(set(forbidden)), sorted(set(markers)))


def explainability_compliance_check(
    module_root: Optional[str] = None,
) -> ComplianceResult:
    """Verifikasi kepatuhan Explainability Experience (group EX).

    Memindai modul explainability untuk forbidden judgment/verification
    tokens dan memastikan ada marker presentasi (graph/aggregate/summary).
    """
    base = module_root or os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(base, m) for m in _EXPLAIN_MODULES
             if os.path.exists(os.path.join(base, m))]
    if not files:
        return ComplianceResult(
            group="EX", total_checks=1, passed=0, failed=1,
            messages=("tidak ada modul explainability experience",),
        )
    forbidden_all = []
    markers = False
    checked = 0
    failed = 0
    messages = []
    for path in files:
        clean, forb, marks = _scan_explain_file(path)
        checked += 1
        forbidden_all.extend(forb)
        if marks:
            markers = True
        if not clean:
            failed += 1
            messages.append("forbidden explain token di %s: %s" % (
                os.path.basename(path), ",".join(forb)))
        else:
            messages.append("OK %s" % os.path.basename(path))
    if not markers:
        failed += 1
        messages.append("tidak ada marker presentation explain")
    return ComplianceResult(
        group="EX",
        total_checks=checked + 1,
        passed=checked + 1 - failed,
        failed=failed,
        messages=tuple(messages),
        forbidden_found=tuple(sorted(set(forbidden_all))),
    )


# --- Production Governance Compliance (IP-3.6-A, group PG) ------------------

# Token yang TIDAK BOLEH hadir dalam source Production Governance. Kehadirannya
# menandakan drift ke eksekusi/penerapan governance atau otorisasi operasional
# (melanggar guardrail MISSION-3.6: measure & report readiness, never enforce).
_PG_FORBIDDEN = (
    "enforce_policy", "apply_policy", "grant_access", "revoke_access",
    "spawn_workflow", "kill_workflow", "scale_up", "scale_down",
    "pause_service", "resume_service", "deploy", "rollback",
    "approve_production", "reject_production", "promote_to_prod",
    "issue_credential", "rotate_secret", "failover_now",
    "execute_governance", "perform_governance", "authorize_action",
)

# Marker positif: kosa kata pengukuran/pelaporan kesiapan yang DIOLEHKAN.
_PG_ALLOWED = (
    "profile", "readiness", "compliance", "baseline", "assess",
    "validate", "verify", "measure", "status", "report", "check",
    "score", "evidence", "snapshot", "present", "read", "aggregate",
)

# Modul Production Governance (Track A MISSION-3.6).
_PG_MODULES = (
    "production_governance.py",
)


def _scan_pg_file(path: str):
    """Scan satu file production governance: (clean, forbidden_hits, markers)."""
    import ast as _ast
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = _ast.parse(f.read(), filename=path)
        except SyntaxError:
            return True, ["<syntax-error>"], []
    forbidden = []
    markers = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for a in node.names:
                if a.asname in _PG_FORBIDDEN:
                    forbidden.append(a.asname)
        if isinstance(node, _ast.ImportFrom):
            for a in node.names:
                if a.name in _PG_FORBIDDEN:
                    forbidden.append(a.name)
        if isinstance(node, _ast.Name):
            if node.id in _PG_FORBIDDEN:
                forbidden.append(node.id)
            elif node.id in _PG_ALLOWED:
                markers.append(node.id)
        if isinstance(node, _ast.Attribute):
            if node.attr in _PG_FORBIDDEN:
                forbidden.append(node.attr)
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            if node.func.id in _PG_FORBIDDEN:
                forbidden.append(node.func.id)
    return (not forbidden, sorted(set(forbidden)), sorted(set(markers)))


def production_governance_compliance_check(
    module_root: Optional[str] = None,
) -> ComplianceResult:
    """Verifikasi kepatuhan Production Governance (group PG).

    Memindai modul production governance untuk forbidden enforcement/ops
    tokens dan memastikan ada marker pengukuran (profile/readiness/compliance/.
    baseline/assess). Menjaga boundary: measure & report, never enforce.
    """
    base = module_root or os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(base, m) for m in _PG_MODULES
             if os.path.exists(os.path.join(base, m))]
    if not files:
        return ComplianceResult(
            group="PG", total_checks=1, passed=0, failed=1,
            messages=("tidak ada modul production governance",),
        )
    forbidden_all = []
    markers = False
    checked = 0
    failed = 0
    messages = []
    for path in files:
        clean, forb, marks = _scan_pg_file(path)
        checked += 1
        forbidden_all.extend(forb)
        if marks:
            markers = True
        if not clean:
            failed += 1
            messages.append("forbidden PG token di %s: %s" % (
                os.path.basename(path), ",".join(forb)))
        else:
            messages.append("OK %s" % os.path.basename(path))
    if not markers:
        failed += 1
        messages.append("tidak ada marker pengukuran production governance")
    return ComplianceResult(
        group="PG",
        total_checks=checked + 1,
        passed=checked + 1 - failed,
        failed=failed,
        messages=tuple(messages),
        forbidden_found=tuple(sorted(set(forbidden_all))),
    )


# --- Platform Operations Compliance (IP-3.6-B, group PO) --------------------

# Token yang TIDAK BOLEH hadir dalam source Platform Operations. Kehadirannya
# menandakan drift ke eksekusi nyata deployment/start/stop (melanggar
# guardrail MISSION-3.6: verify & report ops readiness, never execute ops).
_PO_FORBIDDEN = (
    "do_deploy", "actually_deploy", "perform_deploy", "start_service",
    "stop_service", "restart_service", "kill_process", "spawn_process",
    "write_config", "overwrite_config", "set_environment",
    "export_deployment", "run_init", "execute_boot",
)

# Marker positif: kosa kata verifikasi/inspeksi operasional yang DIOLEHKAN.
_PO_ALLOWED = (
    "validate", "verify", "inspeksi", "check", "deployment",
    "environment", "configuration", "startup", "shutdown",
    "present", "read", "status", "report", "artifact", "factor",
)

# Modul Platform Operations (Track B MISSION-3.6).
_PO_MODULES = (
    "platform_operations.py",
)


def _scan_po_file(path: str):
    """Scan satu file platform operations: (clean, forbidden_hits, markers)."""
    import ast as _ast
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = _ast.parse(f.read(), filename=path)
        except SyntaxError:
            return True, ["<syntax-error>"], []
    forbidden = []
    markers = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for a in node.names:
                if a.asname in _PO_FORBIDDEN:
                    forbidden.append(a.asname)
        if isinstance(node, _ast.ImportFrom):
            for a in node.names:
                if a.name in _PO_FORBIDDEN:
                    forbidden.append(a.name)
        if isinstance(node, _ast.Name):
            if node.id in _PO_FORBIDDEN:
                forbidden.append(node.id)
            elif node.id in _PO_ALLOWED:
                markers.append(node.id)
        if isinstance(node, _ast.Attribute):
            if node.attr in _PO_FORBIDDEN:
                forbidden.append(node.attr)
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            if node.func.id in _PO_FORBIDDEN:
                forbidden.append(node.func.id)
    return (not forbidden, sorted(set(forbidden)), sorted(set(markers)))


def platform_operations_compliance_check(
    module_root: Optional[str] = None,
) -> ComplianceResult:
    """Verifikasi kepatuhan Platform Operations (group PO).

    Memindai modul platform operations untuk forbidden execution-ops tokens
    dan memastikan ada marker verifikasi (
    validate/verify/check/deployment). Menjaga boundary: verify, never
    execute deploy/start/stop.
    """
    base = module_root or os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(base, m) for m in _PO_MODULES
             if os.path.exists(os.path.join(base, m))]
    if not files:
        return ComplianceResult(
            group="PO", total_checks=1, passed=0, failed=1,
            messages=("tidak ada modul platform operations",),
        )
    forbidden_all = []
    markers = False
    checked = 0
    failed = 0
    messages = []
    for path in files:
        clean, forb, marks = _scan_po_file(path)
        checked += 1
        forbidden_all.extend(forb)
        if marks:
            markers = True
        if not clean:
            failed += 1
            messages.append("forbidden PO token di %s: %s" % (
                os.path.basename(path), ",".join(forb)))
        else:
            messages.append("OK %s" % os.path.basename(path))
    if not markers:
        failed += 1
        messages.append("tidak ada marker verifikasi platform operations")
    return ComplianceResult(
        group="PO",
        total_checks=checked + 1,
        passed=checked + 1 - failed,
        failed=failed,
        messages=tuple(messages),
        forbidden_found=tuple(sorted(set(forbidden_all))),
    )


# --- Operational Evidence Compliance (IP-3.6-C, group OE) -------------------

# Token yang TIDAK BOLEH hadir dalam source Operational Evidence. Kehadirannya
# menandakan drift ke pengumpulan sensor/agent atau modifikasi evidence sumber
# (melanggar guardrail MISSION-3.6: consolidate & aggregate, never collect/modify).
_OE_FORBIDDEN = (
    "collect_metric", "probe_runtime", "spawn_sensor", "inject_probe",
    "modify_evidence", "delete_evidence", "overwrite_evidence",
    "write_audit_log", "correlate_live", "attach_agent", "run_collector",
    "emit_metric", "publish_metric",
)

# Marker positif: kosa kata konsolidasi/agregasi evidence yang DIOLEHKAN.
_OE_ALLOWED = (
    "summarize", "aggregate", "consolidate", "summary", "evidence",
    "metrics", "audit", "health", "present", "read", "status",
    "distribution", "average", "report",
)

# Modul Operational Evidence (Track C MISSION-3.6).
_OE_MODULES = (
    "operational_evidence.py",
)


def _scan_oe_file(path: str):
    """Scan satu file operational evidence: (clean, forbidden_hits, markers)."""
    import ast as _ast
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = _ast.parse(f.read(), filename=path)
        except SyntaxError:
            return True, ["<syntax-error>"], []
    forbidden = []
    markers = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for a in node.names:
                if a.asname in _OE_FORBIDDEN:
                    forbidden.append(a.asname)
        if isinstance(node, _ast.ImportFrom):
            for a in node.names:
                if a.name in _OE_FORBIDDEN:
                    forbidden.append(a.name)
        if isinstance(node, _ast.Name):
            if node.id in _OE_FORBIDDEN:
                forbidden.append(node.id)
            elif node.id in _OE_ALLOWED:
                markers.append(node.id)
        if isinstance(node, _ast.Attribute):
            if node.attr in _OE_FORBIDDEN:
                forbidden.append(node.attr)
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            if node.func.id in _OE_FORBIDDEN:
                forbidden.append(node.func.id)
    return (not forbidden, sorted(set(forbidden)), sorted(set(markers)))


def operational_evidence_compliance_check(
    module_root: Optional[str] = None,
) -> ComplianceResult:
    """Verifikasi kepatuhan Operational Evidence (group OE).

    Memindai modul operational evidence untuk forbidden collection/modify
    tokens dan memastikan ada marker konsolidasi (
    summarize/aggregate/consolidate). Menjaga boundary: consolidate, never
    collect/modify evidence sumber.
    """
    base = module_root or os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(base, m) for m in _OE_MODULES
             if os.path.exists(os.path.join(base, m))]
    if not files:
        return ComplianceResult(
            group="OE", total_checks=1, passed=0, failed=1,
            messages=("tidak ada modul operational evidence",),
        )
    forbidden_all = []
    markers = False
    checked = 0
    failed = 0
    messages = []
    for path in files:
        clean, forb, marks = _scan_oe_file(path)
        checked += 1
        forbidden_all.extend(forb)
        if marks:
            markers = True
        if not clean:
            failed += 1
            messages.append("forbidden OE token di %s: %s" % (
                os.path.basename(path), ",".join(forb)))
        else:
            messages.append("OK %s" % os.path.basename(path))
    if not markers:
        failed += 1
        messages.append("tidak ada marker konsolidasi operational evidence")
    return ComplianceResult(
        group="OE",
        total_checks=checked + 1,
        passed=checked + 1 - failed,
        failed=failed,
        messages=tuple(messages),
        forbidden_found=tuple(sorted(set(forbidden_all))),
    )


# --- Production Reliability Compliance (IP-3.6-D, group PR) -----------------

# Token yang TIDAK BOLEH hadir dalam source Production Reliability.
# Kehadirannya menandakan drift ke intervensi nyata (recovery/failover/
# self-heal) yang melanggar guardrail MISSION-3.6 (verify & diagnose, never fix).
_PR_FORBIDDEN = (
    "run_recovery", "execute_rollback", "trigger_failover", "self_heal",
    "restart_component", "scale_up", "patch_runtime", "apply_mitigation",
    "recover_now", "restore_snapshot", "kill_task", "reroute",
)

# Marker positif: kosa kata verifikasi/diagnosis keandalan yang DIOLEHKAN.
_PR_ALLOWED = (
    "verify", "validate", "assess", "summarize", "diagnose",
    "reliability", "recoverability", "stability", "diagnostics",
    "present", "read", "report", "check", "status", "observation",
)

# Modul Production Reliability (Track D MISSION-3.6).
_PR_MODULES = (
    "production_reliability.py",
)


def _scan_pr_file(path: str):
    """Scan satu file production reliability: (clean, forbidden_hits, markers)."""
    import ast as _ast
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = _ast.parse(f.read(), filename=path)
        except SyntaxError:
            return True, ["<syntax-error>"], []
    forbidden = []
    markers = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for a in node.names:
                if a.asname in _PR_FORBIDDEN:
                    forbidden.append(a.asname)
        if isinstance(node, _ast.ImportFrom):
            for a in node.names:
                if a.name in _PR_FORBIDDEN:
                    forbidden.append(a.name)
        if isinstance(node, (_ast.FunctionDef, _ast.ClassDef)):
            if node.name in _PR_FORBIDDEN:
                forbidden.append(node.name)
            for m in _PR_ALLOWED:
                if node.name == m or node.name.startswith(m + "_"):
                    markers.append(node.name)
                    break
        if isinstance(node, _ast.Name):
            if node.id in _PR_FORBIDDEN:
                forbidden.append(node.id)
            elif node.id in _PR_ALLOWED:
                markers.append(node.id)
        if isinstance(node, _ast.Attribute):
            if node.attr in _PR_FORBIDDEN:
                forbidden.append(node.attr)
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            if node.func.id in _PR_FORBIDDEN:
                forbidden.append(node.func.id)
    return (not forbidden, sorted(set(forbidden)), sorted(set(markers)))


def production_reliability_compliance_check(
    module_root: Optional[str] = None,
) -> ComplianceResult:
    """Verifikasi kepatuhan Production Reliability (group PR).

    Memindai modul production reliability untuk forbidden intervention tokens
    dan memastikan ada marker verifikasi/diagnosis.
    Menjaga boundary: verify & diagnose, never fix.
    """
    base = module_root or os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(base, m) for m in _PR_MODULES
             if os.path.exists(os.path.join(base, m))]
    if not files:
        return ComplianceResult(
            group="PR", total_checks=1, passed=0, failed=1,
            messages=("tidak ada modul production reliability",),
        )
    forbidden_all = []
    markers = False
    checked = 0
    failed = 0
    messages = []
    for path in files:
        clean, forb, marks = _scan_pr_file(path)
        checked += 1
        forbidden_all.extend(forb)
        if marks:
            markers = True
        if not clean:
            failed += 1
            messages.append("forbidden PR token di %s: %s" % (
                os.path.basename(path), ",".join(forb)))
        else:
            messages.append("OK %s" % os.path.basename(path))
    if not markers:
        failed += 1
        messages.append("tidak ada marker verifikasi production reliability")
    return ComplianceResult(
        group="PR",
        total_checks=checked + 1,
        passed=checked + 1 - failed,
        failed=failed,
        messages=tuple(messages),
        forbidden_found=tuple(sorted(set(forbidden_all))),
    )


# --- Mission Certification Compliance (IP-3.6-E, group MC) ------------------

# Token yang TIDAK BOLEH hadir dalam source Mission Certification.
# Kehadirannya menandakan drift ke pengambilan keputusan architecture/
# pemberian status Operational (melanggar guardrail: assessment, not authority).
_MC_FORBIDDEN = (
    "declare_operational", "grant_operational", "authorize_mission",
    "approve_mission", "decide_architecture", "enforce_certification",
    "border_override", "override_guardrail", "issue_authority",
    "grant_authority", "adjudicate", "command_deploy",
)

# Marker positif: kosa kata penilaian/verifikasi misi yang DIOLEHKAN.
_MC_ALLOWED = (
    "certify", "certification", "assessment", "readiness", "regression",
    "report", "recommendation", "verify", "measure", "present", "read",
    "aggregate", "evidence",
)

# Modul Mission Certification (Track E MISSION-3.6).
_MC_MODULES = (
    "mission_certification.py",
)


def _scan_mc_file(path: str):
    """Scan satu file mission certification: (clean, forbidden_hits, markers)."""
    import ast as _ast
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = _ast.parse(f.read(), filename=path)
        except SyntaxError:
            return True, ["<syntax-error>"], []
    forbidden = []
    markers = []
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for a in node.names:
                if a.asname in _MC_FORBIDDEN:
                    forbidden.append(a.asname)
        if isinstance(node, _ast.ImportFrom):
            for a in node.names:
                if a.name in _MC_FORBIDDEN:
                    forbidden.append(a.name)
        if isinstance(node, (_ast.FunctionDef, _ast.ClassDef)):
            if node.name in _MC_FORBIDDEN:
                forbidden.append(node.name)
            for m in _MC_ALLOWED:
                if node.name == m or node.name.startswith(m + "_"):
                    markers.append(node.name)
                    break
        if isinstance(node, _ast.Name):
            if node.id in _MC_FORBIDDEN:
                forbidden.append(node.id)
            elif node.id in _MC_ALLOWED:
                markers.append(node.id)
        if isinstance(node, _ast.Attribute):
            if node.attr in _MC_FORBIDDEN:
                forbidden.append(node.attr)
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            if node.func.id in _MC_FORBIDDEN:
                forbidden.append(node.func.id)
    return (not forbidden, sorted(set(forbidden)), sorted(set(markers)))


def mission_certification_compliance_check(
    module_root: Optional[str] = None,
) -> ComplianceResult:
    """Verifikasi kepatuhan Mission Certification (group MC).

    Memindai modul mission certification untuk forbidden authority tokens
    dan memastikan ada marker penilaian (certify/assessment/readiness).
    Menjaga boundary: assessment & report, never grant authority.
    """
    base = module_root or os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join(base, m) for m in _MC_MODULES
             if os.path.exists(os.path.join(base, m))]
    if not files:
        return ComplianceResult(
            group="MC", total_checks=1, passed=0, failed=1,
            messages=("tidak ada modul mission certification",),
        )
    forbidden_all = []
    markers = False
    checked = 0
    failed = 0
    messages = []
    for path in files:
        clean, forb, marks = _scan_mc_file(path)
        checked += 1
        forbidden_all.extend(forb)
        if marks:
            markers = True
        if not clean:
            failed += 1
            messages.append("forbidden MC token di %s: %s" % (
                os.path.basename(path), ",".join(forb)))
        else:
            messages.append("OK %s" % os.path.basename(path))
    if not markers:
        failed += 1
        messages.append("tidak ada marker penilaian mission certification")
    return ComplianceResult(
        group="MC",
        total_checks=checked + 1,
        passed=checked + 1 - failed,
        failed=failed,
        messages=tuple(messages),
        forbidden_found=tuple(sorted(set(forbidden_all))),
    )
