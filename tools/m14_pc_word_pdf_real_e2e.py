r"""M14 Real E2E — Windows PC Ward (Word/PDF) terhadap file nyata.

Membuktikan M14-009/010/011/012 terhadap file .docx/.pdf NYATA di mesin
(pengguna Van) via jalur M14 murni:

  - M14-010 WindowsPCWard:  observe (disk free + probe file) + diagnose
  - M14-011 WordInvestigator: struktur .docx read-only (tanpa isi)
  - M14-012 PDFPerformanceInvestigator: performa PDF read-only (tanpa isi)

Design: read-only. SAM TIDAK membaca isi dokumen - hanya metadata + signature
header. Privasi terjamin. Hasil = evidence + audit artifact.

Cara pakai:
  python tools/m14_pc_word_pdf_real_e2e.py --target <direktori-berisi-docx-pdf>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.delegated_authority.real_pdf_investigation import PDFPerformanceInvestigator
from sam.delegated_authority.real_windows_pc_ward import WindowsPCWard
from sam.delegated_authority.real_word_investigation import WordInvestigator


def run(target_dir: str) -> dict:
    started = time.time()

    # --- M14-010 PC Ward: observe + diagnose (sync) ---
    ward = WindowsPCWard(target_dir=target_dir)
    diagnosis = ward.observe()
    pc = {
        "ward_id": "pc",
        "target_dir": target_dir,
        "disk_total_bytes": diagnosis.disk_total_bytes,
        "disk_free_bytes": diagnosis.disk_free_bytes,
        "disk_free_pct": round(
            (diagnosis.disk_free_bytes / diagnosis.disk_total_bytes) * 100, 2
        ) if diagnosis.disk_total_bytes else None,
        "issues": list(diagnosis.issues),
        "probed_files": [f.as_dict() for f in diagnosis.files],
    }

    # --- M14-011 / M14-012: investigate tiap file nyata (read-only) ---
    word_inv = WordInvestigator()
    pdf_inv = PDFPerformanceInvestigator()
    investigations = []
    for f in diagnosis.files:
        if f.ext == ".docx":
            investigations.append(word_inv.investigate(f.path).as_dict())
        elif f.ext == ".pdf":
            investigations.append(pdf_inv.investigate(f.path).as_dict())

    elapsed = round(time.time() - started, 3)
    result = {
        "milestone": "M14-009/010/011/012",
        "claim": "REAL_E2E_PC_WORD_PDF",
        "environment": {
            "host": os.environ.get("COMPUTERNAME", "unknown"),
            "python": sys.version.split()[0],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
        "pc_ward": pc,
        "investigations": investigations,
        "summary": {
            "probed": len(diagnosis.files),
            "valid_sig": sum(1 for f in diagnosis.files if f.valid_signature),
            "invalid_sig": sum(1 for f in diagnosis.files
                                if not f.valid_signature and f.ext in (".docx", ".pdf")),
            "investigated_word": sum(1 for i in investigations
                                       if os.path.splitext(i["path"])[1].lower() == ".docx"),
            "investigated_pdf": sum(1 for i in investigations
                                     if os.path.splitext(i["path"])[1].lower() == ".pdf"),
            "elapsed_seconds": elapsed,
        },
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="Direktori berisi .docx/.pdf nyata")
    ap.add_argument("--out-dir", default="docs/engineering/state/M14", help="dir evidence")
    args = ap.parse_args()

    if not os.path.isdir(args.target):
        print(f"ERROR: target bukan direktori: {args.target}")
        return 2

    result = run(args.target)
    print(f"[PC] probed={result['summary']['probed']} "
          f"valid_sig={result['summary']['valid_sig']} "
          f"invalid_sig={result['summary']['invalid_sig']}")
    print(f"[PC] disk_free_pct={result['pc_ward']['disk_free_pct']} "
          f"issues={len(result['pc_ward']['issues'])}")

    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    evidence_path = os.path.join(out_dir, "M14_PC_WORD_PDF_real_evidence.json")
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Evidence saved: {evidence_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
