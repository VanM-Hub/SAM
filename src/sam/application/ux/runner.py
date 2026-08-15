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

# Repo test default utk GitHub mutation (repo TEST, bukan production).
DEFAULT_TEST_REPO = "VanM-Hub/test-issues"


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


class UnsupportedOperationError(Exception):
    """Operasi belum dibuka jalur eksekusinya di runner (jujur: BLOCKED)."""


def _detail_of_result(result: Dict[str, Any]) -> str:
    return (
        result.get("detail")
        or result.get("error")
        or result.get("message")
        or "eksekusi selesai"
    )


def run_browser_mission(
    operation: str,
    url: str,
    audit: Optional[AuditTrail] = None,
    approval_reason: str = "",
) -> Dict[str, Any]:
    """Jalankan read-only browser fetch/render via canonical connector.

    Memakai RealBrowserConnector -> RealExecutionHarness (single authority),
    bukan adapter langsung. Read-only: TIDAK mengubah state eksternal.
    """
    from sam.execution_runtime.canonical_browser_connector import RealBrowserConnector
    conn = RealBrowserConnector(audit=audit)
    result = conn.execute(operation=operation, url=url, approval_reason=approval_reason)
    ok = bool(result.get("ok"))
    return {
        "ok": ok,
        "operation": f"browser/{operation}",
        "target": url,
        "timeline": [{"stage": "web.fetch", "ok": ok, "operation": f"browser/{operation}",
                       "target": url, "detail": _detail_of_result(result) if ok else None,
                       "blocked": None if ok else (not result.get("ok"))}],
        "detail": _detail_of_result(result) if ok else "browser gagal: " + _detail_of_result(result),
    }


def run_http_mission(
    endpoint: str,
    params: Dict[str, Any],
    audit: Optional[AuditTrail] = None,
    approval_reason: str = "",
) -> Dict[str, Any]:
    """Jalankan read-only HTTP GET via canonical connector (mirip M7-001/M8-006)."""
    from sam.execution_runtime.canonical_http_connector import RealHttpConnector
    conn = RealHttpConnector(audit=audit)
    result = conn.execute(endpoint_name=endpoint, params=params, approval_reason=approval_reason)
    ok = bool(result.get("ok"))
    return {
        "ok": ok,
        "operation": f"http/{endpoint}",
        "target": endpoint,
        "timeline": [{"stage": "http.get", "ok": ok, "operation": f"http/{endpoint}",
                       "target": endpoint, "detail": _detail_of_result(result) if ok else None,
                       "blocked": None if ok else (not result.get("ok"))}],
        "detail": _detail_of_result(result) if ok else "http gagal: " + _detail_of_result(result),
    }


def run_environment_observation_mission(subject_id: str = "local-machine"):
    """Jalankan observasi environment via EnvironmentObservationAdapter (read-only).

    Memakai EnvironmentDiscovery (mesin real M14) melalui kontrak
    ObservationTarget/Adapter — bukan executor kedua, bukan import harness.
    EnvironmentDiscovery adalah implementation yang DIAMATI, bukan Ward/Citizen
    baru (semantic boundary dikunci Van R1-002).

    Mengembalikan dict bentuk timeline yg dipahami service/UI:
      {ok, operation, target, timeline:[{stage: environment.observe,...}],
       detail, evidence}
    """
    from sam.ward.capability.contracts import SubjectRef
    from sam.ward.adapters.environment_observation import EnvironmentObservationAdapter

    subject = SubjectRef(subject_id=subject_id, subject_type="citizen",
                         kind="environment", name="local-machine")
    adapter = EnvironmentObservationAdapter(subject=subject)
    obs = adapter.observe(capability="observe")

    ev = (obs.evidence if hasattr(obs, "evidence") else {}) or {}
    failures = ev.get("failures") or []
    sources = ev.get("sources") or []
    ok = bool(obs.successful)
    stage_detail = (
        "Menemukan {} entitas environment nyata dari sumber: {}. Probe gagal: {}."
        .format(ev.get("entity_count", 0), ", ".join(sources) or "-",
                ", ".join(f.get("source", "") for f in failures) or "-")
        if ok
        else "environment discovery tidak menghasilkan entitas (probe kosong/gagal)"
    )
    return {
        "ok": ok,
        "operation": "environment.observe",
        "target": subject_id,
        "timeline": [{
            "stage": "environment.observe",
            "ok": ok,
            "blocked": None if ok else True,
            "detail": stage_detail,
            "evidence": ev,
            "scrubbed": {"ok": ok, "entity_count": ev.get("entity_count", 0),
                          "sources": sources, "failures": failures},
        }],
        "detail": stage_detail,
        "evidence": ev,
    }


def run_mission(
    operation: str,
    target: Optional[str] = None,
    audit: Optional[AuditTrail] = None,
    artifact_dir: str = "docs/engineering/reports",
    repo: Optional[str] = None,
    approval_reason: str = "",
) -> Dict[str, Any]:
    """Satu dispatcher eksekusi — pilih eksekutor berdasarkan `operation`.

    Ini BUKAN executor kedua: setiap cabang memanggil connector canonical
    (RealExecutionHarness / m8 mission framework) yang sudah terbukti. HANYA
    operasi yang telah dibuka jalurnya yang dieksekusi; lainnya ->
    UnsupportedOperationError (jujur BLOCKED, 0 side effect).

    Dibuka bertahap (aman dulu):
      - github.create_issue -> m8_002_build (PROVEN M8-006/M9)
      - web.open / web.get  -> RealBrowserConnector (read-only)
      - http.<endpoint>     -> RealHttpConnector (read-only)
      - (email.send / db.write / process.run) -> BELUM dibuka -> BLOCKED
    """
    op = (operation or "").strip()
    if op.startswith("github."):
        REPO = repo or target or DEFAULT_TEST_REPO
        return run_github_real_mission(repo=REPO, audit=audit, artifact_dir=artifact_dir)
    if op.startswith("environment."):
        # R1-002: read-only observasi environment nyata (periksa komputer).
        # target = identitas subjek (default local-machine).
        subject_id = (target or "").strip() or "local-machine"
        return run_environment_observation_mission(subject_id=subject_id)
    if op.startswith("web."):
        url = (target or "").strip()
        if not url:
            raise UnsupportedOperationError("web.open butuh URL target")
        # Sanitasi: Gemma bisa membungkus domain dgn kurung siku (mis. [example.com]).
        url = url.strip("[]()").strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url  # normalisasi: bisa jadi domain mentah
        # fetch_url = HTTP read-only tanpa butuh driver browser (driver
        # playwright/selenium belum terpasang). render ditunda sampai driver ada.
        return run_browser_mission("fetch_url", url, audit=audit, approval_reason=approval_reason)
    if op.startswith("http."):
        endpoint = op.split(".", 1)[1]
        return run_http_mission(endpoint, {}, audit=audit, approval_reason=approval_reason)
    raise UnsupportedOperationError(
        f"Operasi '{op}' belum dibuka untuk eksekusi nyata (BLOCKED, 0 side effect)."
    )


def classify_mission_outcome(result: Dict[str, Any]) -> Dict[str, str]:
    """Map hasil Mission.run() ke state UI (failure semantics, M9-005).

    Mengembalikan {"status": ..., "failure_kind": ..., "message": ...}.
    status: BLOCKED/FAILED/COMPLETED.
    message: bahasa manusia untuk UI.

    GENERIK (B): tidak lagi hardcoded GitHub. Mendeteksi connector dari stage
    pada timeline (github_api -> GitHub; web.fetch -> web; http.get -> http).
    Bila tidak ada stage eksekusi -> FAILED.
    """
    timeline = result.get("timeline", []) or []
    if not timeline:
        return {
            "status": "failed",
            "failure_kind": "failed",
            "message": "mission tidak menghasilkan langkah sama sekali",
        }

    # Deteksi connector utama dari stage eksekusi pada timeline (B).
    _exec_stage = next(
        (t for t in timeline
         if t.get("stage") in ("github_api", "web.fetch", "http.get",
                                "environment.observe", "execute", "act")
         and (t.get("ok") is not None or t.get("blocked") is not None)),
        None,
    )
    if _exec_stage is None:
        _exec_stage = next(
            (t for t in timeline if t.get("stage") not in ("investigate", "verify")),
            None,
        )
    if _exec_stage is None:
        return {
            "status": "failed",
            "failure_kind": "failed",
            "message": "mission tidak menghasilkan langkah eksekusi",
        }

    conn = _exec_stage.get("stage", "execute")
    _label = {
        "github_api": "GitHub",
        "web.fetch": "membaca halaman web",
        "http.get": "panggilan HTTP",
        "environment.observe": "observasi environment",
    }.get(conn, "eksekusi")
    _blocked_msg = {
        "github_api": ("GitHub tidak dapat digunakan karena GITHUB_TOKEN tidak "
                        "tersedia atau GITHUB_TEST_REPO kosong."),
        "web.fetch": "Membaca halaman web terblokir (network/driver tidak tersedia).",
        "http.get": "Panggilan HTTP terblokir (endpoint/kredensial).",
        "environment.observe": "Observasi environment terblokir (probe tidak menghasilkan entitas).",
    }.get(conn, "Eksekusi terblokir (0 side effect).")

    if _exec_stage.get("blocked"):
        return {
            "status": "blocked",
            "failure_kind": "blocked",
            "message": _blocked_msg,
        }
    if not _exec_stage.get("ok"):
        detail = _exec_stage.get("detail") or "menolak permintaan"
        return {
            "status": "failed",
            "failure_kind": "failed",
            "message": f"{_label} gagal: {detail}",
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
        "message": _exec_stage.get("detail") or f"{_label} berhasil",
    }
