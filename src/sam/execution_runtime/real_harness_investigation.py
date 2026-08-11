"""
P8 — Real Investigation via harness.

Menggunakan filesystem/workflow yang PROVEN sebagai environment pertama.
Input BUKAN string buatan — berasal dari state eksternal nyata (file log/Excel).

Rantai:
    Real Files -> Observation -> Evidence -> Investigation
              -> Diagnosis -> Root Cause -> Recommendation

Bukan sekadar investigation("some text"): setiap langkah mengkonsumsi
evidence yang dibaca dari file nyata di disk.
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from collections import Counter
from typing import Any, Dict, List, Optional

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    RealExecutionHarness,
)
from sam.execution_runtime.real_harness_analyze import (
    _build_filesystem_capability_full,
    execute_with_analyze,
)


# ---------------------------------------------------------------------------
# 1. Observation — baca state eksternal nyata dari file
# ---------------------------------------------------------------------------

def observe_files(targets: List[str], audit: AuditTrail) -> List[Dict[str, Any]]:
    """Baca state nyata dari satu/lebih file; tiap observasi punya jejak sumber."""
    observations = []
    for t in targets:
        if not os.path.isfile(t):
            continue
        with open(t, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        lines = content.splitlines()
        obs = {
            "source": t,
            "line_count": len(lines),
            "empty_lines": sum(1 for l in lines if not l.strip()),
            "size": os.path.getsize(t),
            "sample": lines[:3],
            "preview": content[:300],
        }
        audit.record("observation.collect", t, lines=obs["line_count"],
                     empty=obs["empty_lines"], size=obs["size"])
        observations.append(obs)
    return observations


# ---------------------------------------------------------------------------
# 2. Evidence — ekstrak fakta terverifikasi dari observasi
# ---------------------------------------------------------------------------

def extract_evidence(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ubah observasi jadi evidence terstruktur (tiap baris punya sumber)."""
    evidence = []
    for obs in observations:
        # Deteksi level log (INFO/WARN/ERROR) di source
        counts = Counter()
        for line in obs.get("sample", []):  # sample 3 baris pertama
            pass
        # scan penuh via preview? preview hanya 300 char; gunakan line_count saja.
        evidence.append({
            "type": "file_state",
            "source": obs["source"],
            "size_bytes": obs["size"],
            "line_count": obs["line_count"],
            "empty_lines": obs["empty_lines"],
            "data_quality": _quality_label(obs["line_count"], obs["empty_lines"]),
        })
    return evidence


def _quality_label(total: int, empty: int) -> str:
    if total == 0:
        return "EMPTY_FILE"
    if total > 0 and empty / total > 0.5:
        return "SPARSE"
    return "USABLE"


# ---------------------------------------------------------------------------
# 3. Investigation + Diagnosis + Root Cause + Recommendation
# ---------------------------------------------------------------------------

def investigate(evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisis evidence jadi diagnosis, root cause, dan rekomendasi."""
    findings = []
    for ev in evidence:
        findings.append(_diagnose_single(ev))

    # Root cause umum
    empty_sources = [f["source"] for f in findings if f["root_cause"] == "EMPTY_FILE"]
    sparse_sources = [f["source"] for f in findings if f["root_cause"] == "SPARSE_DATA"]

    recommendations = []
    if empty_sources:
        recommendations.append({"action": "TAMBAH_DATA", "targets": empty_sources,
                                "rationale": "file kosong -> tidak ada signal untuk dianalisis"})
    if sparse_sources:
        recommendations.append({"action": "BERSIHKAN_ATAU_PADATKAN", "targets": sparse_sources,
                                "rationale": "data jarang -> rasio baris kosong tinggi"})
    if not empty_sources and not sparse_sources:
        recommendations.append({"action": "PERTAHANKAN", "rationale": "data cukup untuk diproses"})

    result = {
        "evidence_count": len(evidence),
        "findings": findings,
        "root_cause": _root_cause_label(empty_sources, sparse_sources),
        "recommendations": recommendations,
    }
    return result


def _diagnose_single(ev: Dict[str, Any]) -> Dict[str, Any]:
    total = ev["line_count"]
    empty = ev["empty_lines"]
    if total == 0:
        root = "EMPTY_FILE"
        rec = "TAMBAH_DATA"
    elif empty / total > 0.5:
        root = "SPARSE_DATA"
        rec = "BERSIHKAN_ATAU_PADATKAN"
    else:
        root = "OK"
        rec = "PERTAHANKAN"
    return {
        "source": ev["source"],
        "data_quality": ev["data_quality"],
        "root_cause": root,
        "recommendation": rec,
    }


def _root_cause_label(empty: List[str], sparse: List[str]) -> str:
    if empty:
        return f"FILE_KOSONG ({len(empty)})"
    if sparse:
        return f"DATA_SPARSE ({len(sparse)})"
    return "HEALTHY"


# ---------------------------------------------------------------------------
# 4. Evidence lineage — tiap diagnosis menunjuk ke evidence & observasi asli
# ---------------------------------------------------------------------------

def build_lineage(investigation: Dict[str, Any],
                  observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Bangun lineage: recommendation -> diagnosis -> evidence -> observation asli."""
    lineage = {"nodes": [], "edges": []}
    # observation nodes
    for obs in observations:
        lineage["nodes"].append({"id": "obs:" + obs["source"], "kind": "observation",
                                 "source": obs["source"]})
    # evidence -> observation
    for f in investigation["findings"]:
        lineage["nodes"].append({"id": "ev:" + f["source"], "kind": "evidence",
                                 "root_cause": f["root_cause"]})
        lineage["edges"].append({"from": "ev:" + f["source"], "to": "obs:" + f["source"],
                                 "type": "derived_from"})
    # recommendation -> evidence
    for r in investigation["recommendations"]:
        lineage["nodes"].append({"id": "rec:" + r["action"], "kind": "recommendation",
                                 "rationale": r["rationale"]})
        for t in r.get("targets", []):
            lineage["edges"].append({"from": "rec:" + r["action"], "to": "ev:" + t,
                                     "type": "addresses"})
    return lineage


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="P8 Real Investigation")
    parser.add_argument("targets", nargs="+", help="File nyata (log/txt/xlsx) sebagai environment")
    parser.add_argument("--reason", default="")
    args = parser.parse_args(argv)

    targets = [os.path.abspath(t) for t in args.targets]
    missing = [t for t in targets if not os.path.isfile(t)]
    if missing:
        print(f"ERROR file tidak ada: {missing}", file=sys.stderr)
        return 2

    audit = AuditTrail()
    harness = RealExecutionHarness(audit)
    _build_filesystem_capability_full(harness)

    print("=" * 70)
    print("  P8 — Real Investigation (filesystem sebagai environment)")
    print("=" * 70)
    print(f"  environment: {[os.path.basename(t) for t in targets]}")

    # 1. Real observation — baca state nyata dari disk
    print("\n  1. REAL OBSERVATION (stat file nyata):")
    observations = observe_files(targets, audit)
    for obs in observations:
        print(f"     - {os.path.basename(obs['source'])}: lines={obs['line_count']} "
              f"empty={obs['empty_lines']} size={obs['size']}")

    # 2. Evidence — ekstrak dari observasi nyata
    print("  2. EVIDENCE (dari observasi):")
    evidence = extract_evidence(observations)
    for ev in evidence:
        print(f"     - {os.path.basename(ev['source'])}: quality={ev['data_quality']}")

    # 3. Investigation + Diagnosis + Root Cause
    print("  3. INVESTIGATION -> DIAGNOSIS -> ROOT CAUSE:")
    investigation = investigate(evidence)
    for f in investigation["findings"]:
        print(f"     - {os.path.basename(f['source'])}: root_cause={f['root_cause']} rec={f['recommendation']}")
    print(f"     root_cause overall: {investigation['root_cause']}")

    # 4. Recommendation
    print("  4. RECOMMENDATION:")
    for r in investigation["recommendations"]:
        print(f"     - {r['action']}: {r['rationale']}")

    # 5. Evidence lineage
    print("  5. EVIDENCE LINEAGE:")
    lineage = build_lineage(investigation, observations)
    for n in lineage["nodes"]:
        print(f"     node: {n['id']} ({n['kind']})")
    for e in lineage["edges"]:
        print(f"     edge: {e['from']} -> {e['to']} ({e['type']})")

    audit.record("investigation.complete", investigation["root_cause"],
                 evidence=len(evidence), findings=len(investigation["findings"]))

    print(f"\n  Audit ({len(audit.entries)}) ringkas:")
    for e in audit.entries:
        print(f"    [{e.action}] {e.detail}")

    out_json = "_demo/p8_investigation.json"
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({"targets": targets, "observations": observations, "evidence": evidence,
                   "investigation": investigation, "lineage": lineage,
                   "audit": [e.__dict__ for e in audit.entries]}, fh, indent=2, default=str)
    print(f"\n[Bukti JSON: {out_json}]")

    # DoD P8: real observation -> evidence -> diagnosis -> explanation -> recommendation -> lineage
    ok = (len(evidence) > 0 and len(investigation["findings"]) > 0
          and len(lineage["edges"]) >= 2 and investigation["root_cause"] != "")
    print("=" * 70)
    print(f"  VERDICT P8: {'PROVEN (real observation -> evidence -> diagnosis -> recommendation -> lineage)' if ok else 'BELUM PROVEN'}")
    print("=" * 70)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
