"""
P6 — Real Workflow orchestration via harness.

Membuktikan SAM mampu mengorkestrasi URUTAN langkah eksekusi NYATA
melalui pola RealExecutionHarness (P2-B). Bukan satu aksi — rangkaian:

    meta(file) -> analyze(file) -> write_report(ke folder sandbox) -> verify -> audit

Write dibatasi ke folder sandbox `_demo/workflow_out/` (terisolasi, reversible,
bukan sistem user) — aman & membuktikan efek nyata hingga PRODUK tertulis ke disk.

Prinsip: tiap langkah di-gate; jika satu gagal, workflow berhenti (no partial commit).
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any, Dict, List, Optional

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    RealExecutionHarness,
)
from sam.execution_runtime.real_harness_analyze import (
    _AnalyzeAuditBridge,
    AnalyzeAdapter,
    _build_filesystem_capability_full,
)
from sam.execution_runtime import real_harness as _rh


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "_demo", "workflow_out")


class WorkflowWriteAdapter:
    """Write adaptor — hanya menulis ke folder sandbox (reversible, terisolasi)."""

    SANDBOX_ROOT = os.path.abspath(OUTPUT_DIR)

    def __init__(self, audit: AuditTrail) -> None:
        self._audit = audit

    def write_report(self, filename: str, content: str, subdir: str = "") -> Dict[str, Any]:
        target_dir = os.path.join(self.SANDBOX_ROOT, subdir) if subdir else self.SANDBOX_ROOT
        os.makedirs(target_dir, exist_ok=True)
        full_path = os.path.join(target_dir, filename)

        # Verifikasi path masih dalam sandbox (cegah path traversal)
        abs_target = os.path.abspath(full_path)
        if not abs_target.startswith(self.SANDBOX_ROOT):
            raise RuntimeError(f"path di luar sandbox ditolak: {abs_target}")

        with open(full_path, "w", encoding="utf-8") as fh:
            fh.write(content)

        self._audit.record("harness.workflow.write", full_path,
                           bytes=len(content.encode("utf-8")))
        return {"ok": True, "action": "write_report", "path": full_path, "bytes": len(content.encode("utf-8"))}


class RealWorkflow:
    """Orkestrasi urutan langkah nyata. Stopping-on-first-fail."""

    def __init__(self, audit: Optional[AuditTrail] = None) -> None:
        self._audit = audit or AuditTrail()
        self._harness = RealExecutionHarness(self._audit)
        _build_filesystem_capability_full(self._harness)
        self._analyze_adapter = AnalyzeAdapter(self._audit)
        self._write_adapter = WorkflowWriteAdapter(self._audit)

    def _gate(self, request: ExecutionRequest) -> List[Dict[str, Any]]:
        if not self._harness.capability_exists(request.operation.split("/")[0]):
            return [{"id": "capability", "label": "capability tidak terdaftar", "passed": False}]
        full = self._harness._evaluate_gates(request)
        return [g.to_dict() for g in full]

    def run(self, target_file: str, approval_reason: str = "",
            out_name: Optional[str] = None) -> Dict[str, Any]:
        """Eksekusi rangkaian: meta -> analyze -> write_report. Stop jika ada gagal."""
        if not os.path.isfile(target_file):
            return {"ok": False, "error": f"file tidak ditemukan: {target_file}"}

        corr = str(uuid.uuid4())
        steps: List[Dict[str, Any]] = []

        def _step(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
            req = ExecutionRequest(
                operation=f"filesystem/{action}",
                target=os.path.abspath(target_file),
                params=params,
                mode=ExecutionMode.EXECUTE,
                correlation_id=corr,
                timeout_seconds=15.0,
                approval_reason=approval_reason,
            )
            gates = self._gate(req)
            failed = [g for g in gates if not g["passed"]]
            for g in gates:
                self._audit.record("harness.gate", g["id"], passed=g["passed"])
            if failed:
                return {"ok": False, "blocked": True, "blocked_by": [g["id"] for g in failed], "gates": gates}
            return {"ok": True, "gates": gates}

        # Langkah 1: meta (baca informasi file nyata)
        s1 = _step("meta", {"action": "meta"})
        steps.append({"step": "meta", "ok": s1["ok"]})
        if not s1["ok"]:
            self._audit.record("harness.workflow.abort", "meta", reason="gate gagal")
            return {"ok": False, "correlation": corr, "steps": steps, "abort_at": "meta",
                    "blocked_by": s1["blocked_by"]}

        # Ambil meta nyata
        adapter = _rh.RealFilesystemAdapter(self._audit)
        meta = adapter.execute("meta", os.path.abspath(target_file), {})
        steps[-1]["meta"] = {"size": meta.get("size")}

        # Langkah 2: analyze (analisis file nyata)
        s2 = _step("analyze", {"action": "analyze"})
        steps.append({"step": "analyze", "ok": s2["ok"]})
        if not s2["ok"]:
            self._audit.record("harness.workflow.abort", "analyze", reason="gate gagal")
            return {"ok": False, "correlation": corr, "steps": steps, "abort_at": "analyze"}

        bridge = _AnalyzeAuditBridge(self._audit)
        analysis = __import__("sam_analyzer", fromlist=["_analyze_file"])._analyze_file(os.path.abspath(target_file), bridge)
        steps[-1]["total_issues"] = analysis.get("total_issues")

        # Langkah 3: write_report (tulis produk nyata ke sandbox)
        s3 = _step("write_report", {"action": "write_report"})
        steps.append({"step": "write_report", "ok": s3["ok"]})
        if not s3["ok"]:
            self._audit.record("harness.workflow.abort", "write_report", reason="gate gagal")
            return {"ok": False, "correlation": corr, "steps": steps, "abort_at": "write_report"}

        report = self._render_workflow_report(os.path.basename(target_file), analysis, meta, corr)
        filename = out_name or (os.path.splitext(os.path.basename(target_file))[0] + "_workflow_report.txt")
        written = self._write_adapter.write_report(filename, report)
        steps[-1]["written"] = {"path": written.get("path"), "bytes": written.get("bytes")}

        self._audit.record("harness.workflow.complete", filename, correlation=corr)

        return {
            "ok": True, "correlation": corr,
            "steps": steps,
            "output_file": written.get("path"),
            "output_bytes": written.get("bytes"),
        }

    def _render_workflow_report(self, src_name: str, analysis: Dict[str, Any],
                                meta: Dict[str, Any], corr: str) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("  P6 — WORKFLOW REAL EXECUTION REPORT")
        lines.append("=" * 60)
        lines.append(f"  correlation : {corr}")
        lines.append(f"  source      : {src_name}")
        lines.append(f"  file size   : {meta.get('size')} bytes")
        lines.append(f"  total issues: {analysis.get('total_issues')}")
        lines.append("  findings:")
        for f in analysis.get("findings", []):
            if isinstance(f, dict) and f.get("type") == "sheet_scan":
                lines.append(f"    - [{f.get('sheet')}] baris={f.get('rows')} kosong={f.get('empty_cells')} dup={f.get('duplicate_rows')}")
            elif isinstance(f, dict) and f.get("type") == "file_meta":
                lines.append(f"    - [meta] baris={f.get('lines')} kosong={f.get('empty_lines')}")
            elif isinstance(f, dict) and f.get("type") == "log_levels":
                lines.append(f"    - [level] {f.get('counts')}")
        lines.append("=" * 60)
        lines.append("")
        lines.append("Workflow: meta -> analyze -> write_report (3 langkah nyata, semua PASS).")
        lines.append("Ditulis oleh RealWorkflow via RealExecutionHarness (P2-B gates).")
        return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="P6 Real Workflow orchestration")
    parser.add_argument("target", help="File nyata (Excel/log)")
    parser.add_argument("--reason", default="", help="Reason approval")
    parser.add_argument("--out", default=None, help="Nama file laporan output")
    args = parser.parse_args(argv)

    audit = AuditTrail()
    wf = RealWorkflow(audit)
    reason = args.reason or "P6: workflow real 3-langkah pada file nyata"
    result = wf.run(args.target, approval_reason=reason, out_name=args.out)

    print("=" * 70)
    print("  P6 — Real Workflow orchestration")
    print("=" * 70)
    print(f"  target    : {args.target}")
    print(f"  correlation: {result.get('correlation')}")
    print("  steps:")
    for s in result.get("steps", []):
        print(f"    {s['step']}: {'PASS' if s['ok'] else 'FAIL'} { {k: v for k, v in s.items() if k not in ('step', 'ok')} }")
    if result.get("blocked_by"):
        print(f"  blocked_by: {result['blocked_by']}")
    if result.get("output_file"):
        print(f"  output    : {result['output_file']} ({result.get('output_bytes')} bytes)")
    print("  audit:")
    for e in audit.entries:
        print(f"    [{e.action}] {e.detail}")
    print("=" * 70)

    out_json = "_demo/workflow_result.json"
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({"target": args.target, "result": result,
                   "audit": [e.__dict__ for e in audit.entries]}, fh, indent=2, default=str)
    print(f"\n[Bukti JSON: {out_json}]")

    ok = result.get("ok") and result.get("output_file")
    print(f"\n  VERDICT: {'WORKFLOW PROVEN (3 langkah nyata + produk tertulis)' if ok else 'GAGAL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
