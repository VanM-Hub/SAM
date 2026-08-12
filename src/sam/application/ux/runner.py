"""runner.py — menjalankan mission nyata lewat jalur canonical (M9-003/006).

Tanggung jawab file ini: SATU — menerjemahkan rencana+approval yang sudah
dikunci oleh service ke pemanggilan mission canonical (m8_mission_framework).
TIDAK membuat executor kedua. TIDAK meng-evaluasi approval/policy sendiri.

Untuk vertical slice M9-001..006 dipakai `m8_002_build` (GitHub real mutation
di repo test, sudah PROVEN M8-002 + M8-006). Setelah rencana ditambah
"approve" user, mission baru dijalankan.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from sam.execution_runtime.m8_mission_framework import m8_002_build
from sam.execution_runtime.real_harness import AuditTrail


def build_github_real_mission(
    repo: str,
    audit: Optional[AuditTrail] = None,
    artifact_dir: str = "docs/engineering/reports",
):
    """Bangun CredentialedMission GitHub real (jalur canonical, tanpa executor kedua)."""
    return m8_002_build(audit or AuditTrail(), artifact_dir, repo=repo)


def run_github_real_mission(
    repo: str,
    audit: Optional[AuditTrail] = None,
    artifact_dir: str = "docs/engineering/reports",
) -> Dict[str, Any]:
    """Jalankan mission GitHub real. Mengembalikan dict Mission.run().

    Failure semantics di-deteksi di sini (read-only dari timeline):
      - stage github_api blocked=True    -> state BLOCKED (credential hilang)
      - stage github_api ok=False        -> state FAILED (HTTP / token invalid)
      - semua ok True                   -> state COMPLETED
      - ada step blocked tapi bukan stage kritis -> RETRYABLE / PARTIAL (kami
        anggap FAILED agar UI jujur tentang outcome).
    """
    mission = build_github_real_mission(repo, audit=audit, artifact_dir=artifact_dir)
    return mission.run()


def classify_mission_outcome(result: Dict[str, Any]) -> Dict[str, str]:
    """Map hasil Mission.run() ke state UI (failure semantics, M9-005).

    Mengembalikan {"status": ..., "failure_kind": ..., "message": ...}.
    status: BLOCKED/FAILED/COMPLETED.
    message: bahasa manusia untuk UI.
    """
    timeline = result.get("timeline", []) or []
    if not timeline:
        return {
            "status": "failed",
            "failure_kind": "failed",
            "message": "mission tidak menghasilkan langkah sama sekali",
        }

    github_step = next(
        (t for t in timeline if t.get("stage") in ("github_api", "execute", "act")
         and (t.get("ok") is not None or t.get("blocked") is not None)),
        None,
    )
    if github_step is None:
        # Fallback: pakai step apa pun yang bukan investigate/verify bila ada real effect.
        github_step = next(
            (t for t in timeline if t.get("stage") not in ("investigate", "verify")),
            None,
        )
    if github_step is None:
        return {
            "status": "failed",
            "failure_kind": "failed",
            "message": "mission tidak menghasilkan langkah eksekusi",
        }

    if github_step.get("blocked"):
        return {
            "status": "blocked",
            "failure_kind": "blocked",
            "message": (
                "GitHub tidak dapat digunakan karena GITHUB_TOKEN tidak tersedia"
                " atau GITHUB_TEST_REPO kosong."
            ),
        }
    if not github_step.get("ok"):
        detail = github_step.get("detail") or "GitHub menolak permintaan"
        return {
            "status": "failed",
            "failure_kind": "failed",
            "message": f"GitHub gagal: {detail}",
        }
    if not result.get("ok"):
        return {
            "status": "failed",
            "failure_kind": "failed",
            "message": "mission selesai sebagian; satu atau lebih langkah tidak ok",
        }
    return {
        "status": "completed",
        "failure_kind": "",
        "message": github_step.get("detail") or "eksekusi nyata berhasil",
    }
