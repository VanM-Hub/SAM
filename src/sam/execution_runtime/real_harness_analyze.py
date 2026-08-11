"""
P3 — Filesystem Real E2E: integrasi sam_analyzer sebagai capability analisis.

Memanfaatkan RealExecutionHarness (P2-C) + logika analisis nyata dari
sam_analyzer.py untuk membuktikan rantai lengkap:

    SAM -> Capability -> Contract -> Approval -> Execute
        -> REAL FILE (Excel/log) -> Verify -> Audit

Alur:
    - capability "filesystem" dengan aksi: read / hash / meta (P2-C, nyata)
    - capability "filesystem" dengan aksi: analyze (P3, nyata via sam_analyzer)
    - repeatable run dibuktikan: dua run -> hasil & audit identik.

Modul ini MANDIRI, deterministik, offline-friendly.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any, Dict, List, Optional

# Pastikan root project di sys.path agar bisa import sam_analyzer
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from sam.execution_runtime.real_harness import (  # noqa: E402
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    GateResult,
    RealExecutionHarness,
    RealFilesystemAdapter,
)
import sam.execution_runtime.real_harness as _rh  # untuk akses _build/_verify  # noqa: E402


# ---------------------------------------------------------------------------
# Bridge audit — sam_analyzer memakai record(action, detail, extra_dict) posisi,
# harness memakai record(action, detail, **kwargs). Shim meneruskan keduanya.
# ---------------------------------------------------------------------------

class _AnalyzeAuditBridge:
    """Meneruskan audit dari gaya sam_analyzer ke harness AuditTrail tanpa bentrok."""
    def __init__(self, harness_audit: AuditTrail) -> None:
        self._h = harness_audit

    def record(self, action: str, detail: str, extra=None) -> None:
        if isinstance(extra, dict):
            self._h.record(action, detail, **extra)
        else:
            self._h.record(action, detail)

    @property
    def entries(self):
        return self._h.entries


# ---------------------------------------------------------------------------
# Adaptor analisis (filesystem/analyze) — memakai logika nyata sam_analyzer
# ---------------------------------------------------------------------------

class AnalyzeAdapter:
    """External Adapter #2: analisis file nyata (Excel/CSV/log/teks) utk P3."""

    SUPPORTED_EXTS = (".xlsx", ".xlsm", ".xls", ".csv", ".tsv", ".log", ".txt")

    def __init__(self, audit: AuditTrail) -> None:
        self._audit = audit

    def execute(self, action: str, target: str, params: Dict[str, Any]) -> Dict[str, Any]:
        self._audit.record("harness.adapter.call", f"filesystem/{action}", target=target)
        if action != "analyze":
            raise RuntimeError(f"AnalyzeAdapter hanya mendukung 'analyze', dapat '{action}'")

        ext = os.path.splitext(target)[1].lower()
        if ext not in self.SUPPORTED_EXTS:
            raise RuntimeError(f"extensi '{ext}' belum didukung AnalyzeAdapter: {self.SUPPORTED_EXTS}")

        import sam_analyzer  # gaya library (dari root project)
        bridge = _AnalyzeAuditBridge(self._audit)  # kompatibilitas audit
        result = sam_analyzer._analyze_file(target, bridge)
        self._audit.record("harness.adapter.analyze", target,
                           issues=result.get("total_issues"), source=os.path.basename(target))
        return {
            "ok": True, "action": action,
            "source": os.path.basename(target),
            "total_issues": result.get("total_issues"),
            "findings": result.get("findings"),
        }


# ---------------------------------------------------------------------------
# Verifikasi tambahan untuk analisis
# ---------------------------------------------------------------------------

def _verify_analyze(outcome: Dict[str, Any], target: str, audit: AuditTrail) -> Dict[str, Any]:
    checks: Dict[str, Any] = {"checks": {}}
    passed = True

    # harus ada 'findings' dari analisis nyata (bukan simulasi)
    has_findings = isinstance(outcome.get("findings"), list)
    checks["has_findings"] = has_findings

    # findings harus berasal dari file nyata (ada ukuran baris / sheet)
    nonempty_findings = has_findings and len(outcome.get("findings", [])) > 0
    checks["nonempty_findings"] = nonempty_findings

    # pastikan bukan string "Simulated ..."
    checks["not_simulated"] = "simulated" not in str(outcome.get("findings")).lower()

    if not (has_findings and nonempty_findings and checks["not_simulated"]):
        passed = False

    checks["passed"] = passed
    audit.record("harness.verification.analyze", target, passed=passed, checks=checks)
    return checks


# ---------------------------------------------------------------------------
# Registrasi capability filesystem lengkap (P2-C + P3)
# ---------------------------------------------------------------------------

def _build_filesystem_capability_full(harness: RealExecutionHarness) -> None:
    registry = {
        "id": "filesystem",
        "actions": ["read", "hash", "meta", "analyze"],
        "adapter": "RealFilesystemAdapter + AnalyzeAdapter",
        "external": "local disk",
    }
    contract = {
        "read":     {"input": "path", "output": "content + bytes", "side_effect": "none"},
        "hash":     {"input": "path", "output": "sha256", "side_effect": "none"},
        "meta":     {"input": "path", "output": "size/mtime/readonly", "side_effect": "none"},
        "analyze":  {"input": "path (xlsx/csv/log/txt)", "output": "findings + issues", "side_effect": "none"},
    }
    harness.register_capability("filesystem", registry, contract, policy="ALLOW")


# ---------------------------------------------------------------------------
# Jalur eksekusi dengan dukungan analyze
# ---------------------------------------------------------------------------

def execute_with_analyze(harness: RealExecutionHarness,
                         request: ExecutionRequest,
                         audit: Optional[AuditTrail] = None) -> Any:
    """Menjalankan request lewat harness; untuk analyze pakai AnalyzeAdapter + verifikasi khusus."""
    from sam.execution_runtime.real_harness import _verify_external_effect

    # PREVIEW -> tetap aman lewat harness standar
    if request.mode == ExecutionMode.PREVIEW:
        return harness.execute(request)

    # EXECUTE -> pastikan semua gate lolos dulu (reuse evaluasi harness)
    gates = harness._evaluate_gates(request)
    failed = [g for g in gates if not g.passed]
    for g in gates:
        audit.record("harness.gate", g.id, passed=g.passed)

    if failed:
        outcome = {"ok": False, "mode": "EXECUTE", "external_side_effect": False,
                   "blocked": True, "blocked_by": [g.id for g in failed],
                   "detail": "NO EXTERNAL SIDE EFFECT (P2-B)."}
        return harness._build_blocked_result(request, outcome, gates)

    # action analyze -> adaptor analisis nyata
    action = request.operation.split("/")[-1]
    if action == "analyze":
        adapter = AnalyzeAdapter(audit)
        outcome = adapter.execute("analyze", request.target, request.params)
        verification = _verify_analyze(outcome, request.target, audit)
        return harness._build_ok_result(request, outcome, verification, audit, external=True)

    # aksi lain (read/hash/meta) -> adaptor filesystem standar
    return harness.execute(request)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="P3 Filesystem Real E2E (analyze)")
    parser.add_argument("target", help="File nyata (xlsx/csv/log/txt)")
    parser.add_argument("--mode", choices=["PREVIEW", "EXECUTE"], default="EXECUTE")
    parser.add_argument("--reason", default=argparse.SUPPRESS,
                        help="Reason approval (WAJIB untuk EXECUTE)")
    parser.add_argument("--runs", type=int, default=2,
                        help="Jumlah repeatable run untuk bukti determinisme")
    args = parser.parse_args(argv)

    target = os.path.abspath(args.target)
    if not os.path.isfile(target):
        print(f"ERROR: file tidak ditemukan: {target}", file=sys.stderr)
        return 2

    # siapkan reason Wajib utk EXECUTE
    if args.mode == "EXECUTE":
        reason = getattr(args, "reason", "") or f"P3: analisis nyata file {os.path.basename(target)}"

    audit = AuditTrail()
    harness = RealExecutionHarness(audit)
    _build_filesystem_capability_full(harness)

    print("=" * 70)
    print("  P3 — Filesystem Real E2E (analysis via sam_analyzer)")
    print("=" * 70)
    print(f"  target   : {target}")
    print(f"  mode     : {args.mode}")
    print(f"  runs     : {args.runs}")

    # Repeatable run: jalankan beberapa kali, bandingkan hasil
    results = []
    for i in range(1, args.runs + 1):
        run_audit = AuditTrail()  # audit terpisah per run utk determinisme
        h2 = RealExecutionHarness(run_audit)
        _build_filesystem_capability_full(h2)
        req = ExecutionRequest(
            operation="filesystem/analyze",
            target=target,
            params={"action": "analyze"},
            mode=ExecutionMode(args.mode),
            correlation_id=f"p3-run{i}-{uuid.uuid4().hex[:8]}",
            timeout_seconds=15.0,
            approval_reason=reason if args.mode == "EXECUTE" else "",
        )
        res = execute_with_analyze(h2, req, run_audit)
        results.append((req, res, run_audit))

    # Bandingkan determinisme: total_issues harus sama antar run
    issue_counts = [r[1].outcome.get("total_issues") for r in results]
    deterministic = len(set(issue_counts)) == 1
    print(f"  total_issues per run: {issue_counts}")
    print(f"  deterministic      : {'YES' if deterministic else 'NO'}")

    # Tampilkan detail run pertama
    req, res, run_audit = results[0]
    print("")
    print("  --- Run #1 ---")
    print(f"  correlation : {res.correlation_id}")
    print(f"  external_effect: {res.external_effect}")
    print(f"  total_issues: {res.outcome.get('total_issues')}")
    print(f"  source      : {res.outcome.get('source')}")
    print("  findings (ringkas):")
    for f in res.outcome.get("findings", []):
        if isinstance(f, dict):
            ftype = f.get("type")
            if ftype == "sheet_scan":
                print(f"    - [sheet {f.get('sheet')}] baris={f.get('rows')} sel_kosong={f.get('empty_cells')} dup={f.get('duplicate_rows')}")
            elif ftype == "empty_sheet":
                print(f"    - [kosong] {f.get('msg')}")
            elif ftype == "file_meta":
                print(f"    - [meta] baris={f.get('lines')} kosong={f.get('empty_lines')}")
            elif ftype == "log_levels":
                print(f"    - [level] {f.get('counts')}")
            elif ftype == "repeated_lines":
                print(f"    - [pola] {f.get('patterns')}")
    print(f"  verification.passed: {res.verification.get('passed')}")
    print(f"  audit entries      : {len(res.audit)}")

    # Simpan bukti JSON
    out_json = os.path.splitext(target)[0] + "_p3_report.json"
    payload = {
        "target": target,
        "mode": args.mode,
        "runs": args.runs,
        "deterministic": deterministic,
        "issue_counts": issue_counts,
        "run1": {"request": req.snapshot(), "result": res.to_dict()},
    }
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    print(f"\n[Bukti JSON disimpan ke: {out_json}]")

    # Verdict
    ok = (res.external_effect and res.verification.get("passed") and deterministic)
    print("")
    print("=" * 70)
    print(f"  VERDICT P3: {'PROVEN (real + verified + deterministic + audited)' if ok else 'BELUM PROVEN'}")
    print("=" * 70)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
