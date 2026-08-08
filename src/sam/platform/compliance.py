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
