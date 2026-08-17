"""runner.py — menjalankan mission nyata lewat jalur canonical (M9-003/006).

Tanggung jawab file ini: SATU — menerjemahkan rencana+approval yang sudah
dikunci oleh service ke pemanggilan mission canonical (m8_mission_framework).
TIDAK membuat executor kedua. TIDAK meng-evaluasi approval/policy sendiri.

Untuk vertical slice M9-001..006 dipakai `m8_002_build` (GitHub real mutation
di repo test, sudah PROVEN M8-002 + M8-006). Setelah rencana ditambah
"approve" user, mission baru dijalankan.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sam.execution_runtime.m8_mission_framework import m8_002_build
from sam.execution_runtime.real_harness import AuditTrail

if TYPE_CHECKING:  # pragma: no cover - hanya utk anotasi tipe
    from sam.ward.capability.contracts import DiagnosisResult

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


def _maybe_resolve_ward(subject_id: str, operation: str, ward_manager) -> Optional[Dict[str, Any]]:
    """W1: Resolve target Ward eksternal (mis. OpenClaw) lewat Ward boundary.

    Dipanggil dari run_mission utk operasi environment.*. Return:
      - None   : target adalah citizen (local-machine dll.) -> jalur existing
                 (EnvironmentDiscovery) dipakai. BUKAN Ward.
      - dict   : hasil observasi Ward (ok/refused) utk dikembalikan langsung.
                 refused/blocked -> {ok:False, blocked:True} (0 mutation).

    alur (Van #7 W1): authenticated tenant -> Ward resolution ->
    status/entrustment -> capability scope -> governance boundary -> adapter
    -> evidence.
    """
    try:
        from sam.ward.manager import WardManager
        if not isinstance(ward_manager, WardManager):
            from sam.ward.wiring import get_ward_manager
            ward_manager = get_ward_manager()
    except Exception:  # noqa: BLE001 - tak ada Ward wiring -> citizen path saja
        ward_manager = None

    if ward_manager is None:
        return None  # Ward subsystem tidak tersedia -> jalur citizen existing

    # local-machine dkk tetap citizen, BUKAN Ward (Van #6).
    if ward_manager.is_citizen_env_target(subject_id):
        return None

    op = (operation or "").strip()
    # W1 scope: hanya environment.observe yg dibuka utk Ward Lab (OpenClaw).
    # investigate/diagnose/recommend pada Ward eksternal -> refused jujur
    # (scope awal read-only observe saja; mutation TIDAK diaktifkan, Van #4).
    if not op.startswith("environment.observe"):
        return {
            "ok": False,
            "operation": op,
            "target": subject_id,
            "blocked": True,
            "timeline": [{
                "stage": op, "ok": False, "blocked": True,
                "detail": f"W1: operation '{op}' pada Ward '{subject_id}' belum dibuka "
                           f"(scope awal hanya environment.observe read-only; lainnya refused, 0 mutation)",
                "evidence": {"verified_read": False, "ward": subject_id},
            }],
            "detail": f"refused: operation '{op}' di luar scope observe W1 utk Ward '{subject_id}'",
            "evidence": {"verified_read": False, "ward": subject_id},
        }

    resolution = ward_manager.auth_ward(subject_id, op)
    if not resolution.ok:
        # fail-closed: tidak ada eksekusi. reason (tenant/status/scope/cross-tenant).
        return {
            "ok": False,
            "operation": op,
            "target": subject_id,
            "blocked": True,
            "timeline": [{
                "stage": "environment.observe", "ok": False, "blocked": True,
                "detail": "refused: " + resolution.reason,
                "evidence": {"verified_read": False, "ward": subject_id,
                              "reason": resolution.reason},
            }],
            "detail": "refused: " + resolution.reason,
            "evidence": {"verified_read": False, "ward": subject_id,
                          "reason": resolution.reason},
        }

    # resolve sukses -> observasi Ward nyata via adapter OpenClaw (reuse M14).
    return _run_ward_openclaw_observe(resolution.subject, subject_id)


def _run_ward_openclaw_observe(subject, subject_label: str) -> Dict[str, Any]:
    """Observasi Ward OpenClaw (read-only) via OpenClawObservationAdapter.

    Adapter ini MEMAKAI OpenClawHealthCollector (M14 canonical) — bukan
    integrasi kedua. Evidence = status komponen NYATA. Bila tak tersedia ->
    honest NOT READY (0 sukses palsu).
    """
    from sam.ward.adapters.openclaw_observation import OpenClawObservationAdapter

    adapter = OpenClawObservationAdapter(subject=subject)
    obs = adapter.observe(capability="observe")
    ev = (obs.evidence if hasattr(obs, "evidence") else {}) or {}
    comps = ev.get("components") or []
    comp_count = ev.get("component_count", len(comps))
    runtime = ev.get("runtime_status") or "unknown"
    gateway_used = bool(ev.get("gateway_used"))
    ok = bool(obs.successful)
    stage_detail = (
        f"OpenClaw Ward {subject_label} diobservasi (runtime={runtime}, "
        f"komponen={comp_count}, gateway={gateway_used})"
        if ok
        else f"OpenClaw Ward {subject_label} tidak tersedia (NOT READY: {obs.error or ''})"
    )
    return {
        "ok": ok,
        "operation": "environment.observe",
        "target": subject_label,
        "ward_subject": subject.as_dict(),
        "timeline": [{
            "stage": "environment.observe", "ok": ok, "blocked": None if ok else True,
            "detail": stage_detail,
            "evidence": {
                "kind": "openclaw_ward_observation",
                "component_count": comp_count,
                "components": comps,
                "runtime_status": runtime,
                "workspace": ev.get("workspace"),
                "gateway_used": gateway_used,
            },
            "scrubbed": {"ok": ok, "component_count": comp_count, "runtime_status": runtime},
        }],
        "detail": stage_detail,
        "evidence": {
            "kind": "openclaw_ward_observation",
            "component_count": comp_count,
            "components": comps,
            "runtime_status": runtime,
            "workspace": ev.get("workspace"),
            "gateway_used": gateway_used,
            "verified_read": ok,
        },
    }


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


def run_environment_investigation_mission(
    subject_id: str = "local-machine",
    observation_evidence: Optional[Dict[str, Any]] = None,
):
    """Jalankan investigasi environment via EnvironmentInvestigationAdapter
    (read-only, R1-003).

    Reuse DiagnosisEngine.investigate() (canonical, M14-PROVEN) melalui kontrak
    InvestigationTarget/InvestigationResult - BUKAN engine kedua. Adapter hanya
    menerjemahkan EntityGraph (dari EnvironmentDiscovery) ke DiagnosisEngine.

    Berhenti di Finding kandidat + evidence + confidence. TIDAK menyimpulkan
    root cause (itu R1-004), TIDAK recommendation, TIDAK mutation.

    Mengembalikan dict bentuk timeline yg dipahami service/UI:
      {ok, operation, target, timeline:[{stage: environment.investigate,...}],
       detail, evidence}
    """
    from sam.ward.capability.contracts import SubjectRef
    from sam.ward.adapters.environment_investigation import (
        EnvironmentInvestigationAdapter,
    )

    subject = SubjectRef(subject_id=subject_id, subject_type="citizen",
                         kind="environment", name="local-machine")
    adapter = EnvironmentInvestigationAdapter(subject=subject)
    result = adapter.investigate(evidence=observation_evidence or {},
                                 capability="investigate")

    findings = list(result.findings or [])
    ok = bool(result.successful)
    if ok and not findings:
        # Investigasi berjalan tapi evidence tidak cukup -> INSUFFICIENT jujur.
        stage_detail = result.summary or (
            "investigasi selesai tanpa temuan kandidat karena evidence tidak cukup")
    else:
        stage_detail = result.summary or (
            "investigasi environment selesai ({} temuan kandidat)".format(len(findings)))

    scrubbed = {
        "ok": ok,
        "finding_count": len(findings),
        "insufficient": bool(ok) and not findings,
        "summary": result.summary or "",
        "evidence_ref": result.evidence_ref or "",
        "error": result.error or "",
    }
    return {
        "ok": ok,
        "operation": "environment.investigate",
        "target": subject_id,
        "timeline": [{
            "stage": "environment.investigate",
            "ok": ok,
            "blocked": None if ok else True,
            "detail": stage_detail,
            "evidence": {
                "kind": "environment_investigation",
                "findings": findings,
                "finding_count": len(findings),
                "insufficient": scrubbed["insufficient"],
                "summary": result.summary or "",
                "evidence_ref": result.evidence_ref or "",
                "error": result.error or "",
            },
            "scrubbed": scrubbed,
        }],
        "detail": stage_detail,
        "evidence": {
            "kind": "environment_investigation",
            "findings": findings,
            "finding_count": len(findings),
            "insufficient": scrubbed["insufficient"],
            "summary": result.summary or "",
            "evidence_ref": result.evidence_ref or "",
            "error": result.error or "",
        },
    }


def run_environment_diagnosis_mission(
    findings: Optional[List[Dict[str, Any]]] = None,
    subject_id: str = "local-machine",
):
    """Jalankan diagnosis environment via EnvironmentDiagnosisAdapter
    (read-only evaluator, R1-004).

    Menerima FINDINGS dari investigasi R1-003 (W1: di-cache service saat misi
    investigate selesai), MENGEKSTRAK selected evidence, lalu menyerahkan ke
    adapter.diagnose().

    Murni evaluator: menilai verdict (causal/candidate/insufficient) atas evidence
    yang SUDAH ada. TIDAK mencari bukti baru (itu investigation ulang, dilarang),
    TIDAK recommendation, TIDAK mutation. Evidence tidak cukup -> INSUFFICIENT jujur.

    Mengembalikan dict bentuk timeline yg dipahami service/UI:
      {ok, operation, target, timeline:[{stage: environment.diagnose,...}],
       detail, evidence}
    """
    from sam.ward.capability.contracts import SubjectRef
    from sam.ward.adapters.environment_diagnosis import (
        EnvironmentDiagnosisAdapter,
    )

    subject = SubjectRef(subject_id=subject_id, subject_type="citizen",
                         kind="environment", name="local-machine")
    selected = _extract_selected_evidence(findings or [])
    adapter = EnvironmentDiagnosisAdapter(subject=subject)
    result = adapter.diagnose(evidence=selected, capability="diagnose")

    verdict = result.verdict
    ok = not result.error  # evaluator sukses; error hanya bila internal
    stage_detail = result.summary or f"diagnosis verdict={verdict}"
    diagnosis = [f.as_dict() for f in result.diagnosis]
    evidence_dict = {
        "kind": "environment_diagnosis",
        "verdict": verdict,
        "confidence": result.confidence,
        "diagnosis": diagnosis,
        "evidence_ref": result.evidence_ref or "",
        "summary": result.summary or "",
        "error": result.error or "",
        "sufficiency": verdict,  # eksplisit: verdict = diagnostic sufficiency
    }
    _canonical = result  # objek DiagnosisResult canonical (R1-005 cache)
    return {
        "ok": ok,
        "operation": "environment.diagnose",
        "target": subject_id,
        "_canonical_diagnosis": _canonical,
        "timeline": [{
            "stage": "environment.diagnose",
            "ok": ok,
            "blocked": None if ok else True,
            "detail": stage_detail,
            "evidence": evidence_dict,
            "scrubbed": {
                "ok": ok,
                "verdict": verdict,
                "confidence": result.confidence,
                "diagnosis": diagnosis,
                "evidence_ref": result.evidence_ref or "",
                "sufficiency": verdict,
            },
        }],
        "detail": stage_detail,
        "evidence": evidence_dict,
    }


def _extract_selected_evidence(
    findings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Ekstrak SELECTED EVIDENCE (flatten) dari findings investigasi R1-003.

    Setiap finding = {..., "evidence": [e.as_dict()]}. Diagnosis menerima
    List evidence (bukan findings mentah - DiagnosisTarget BUKAN salinan
    InvestigationResult). Bila findings kosong -> [] (adapter jawab
    insufficient jujur).
    """
    out: List[Dict[str, Any]] = []
    for f in findings or []:
        for e in (f.get("evidence") or []):
            if isinstance(e, dict):
                out.append(dict(e))
    return out


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


def run_environment_recommendation_mission(
    diagnosis: Optional["DiagnosisResult"] = None,
    subject_id: str = "local-machine",
):
    """Jalankan recommendation environment via EnvironmentRecommendationAdapter
    (read-only, R1-005).

    Menerima DiagnosisResult (R1-004, canonical) - BUKAN findings mentah,
    BUKAN Dict serialized. Adapter menilai verdict dan menyusun rekomendasi
    canonical HANYA bila ada canonical action mapping TERBUKTI; bila tidak,
    causal -> recommendations=[] jujur (fail-closed).

    Tidak import environment, connector, AI, WardGovernor, executor. Berhenti
    di RecommendationResult (STOP). Tidak ada mutation/side effect.

    Mengembalikan dict bentuk timeline yg dipahami service/UI:
      {ok, operation, target, timeline:[{stage: environment.recommend,...}],
       detail, evidence}
    """
    from sam.ward.capability.contracts import SubjectRef
    from sam.ward.adapters.environment_recommendation import (
        EnvironmentRecommendationAdapter,
    )

    subject = SubjectRef(subject_id=subject_id, subject_type="citizen",
                         kind="environment", name="local-machine")
    # BUKAN mengarang: tanpa injection canonical action mapping -> adapter
    # fail-closed jujur (causal -> [] bila tidak ada mapping terbukti).
    adapter = EnvironmentRecommendationAdapter(subject=subject)
    result = adapter.recommend(diagnosis=diagnosis, capability="recommend")

    recommendations = [r.as_dict() for r in result.recommendations]
    ok = not result.error
    stage_detail = result.summary or (
        "recommendation selesai ({} rekomendasi)".format(len(recommendations)))
    evidence_dict = {
        "kind": "environment_recommendation",
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
        "diagnosis_ref": result.diagnosis_ref or "",
        "summary": result.summary or "",
        "error": result.error or "",
    }
    return {
        "ok": ok,
        "operation": "environment.recommend",
        "target": subject_id,
        "timeline": [{
            "stage": "environment.recommend",
            "ok": ok,
            "blocked": None if ok else True,
            "detail": stage_detail,
            "evidence": evidence_dict,
            "scrubbed": {
                "ok": ok,
                "recommendation_count": len(recommendations),
                "recommendations": recommendations,
                "diagnosis_ref": result.diagnosis_ref or "",
            },
        }],
        "detail": stage_detail,
        "evidence": evidence_dict,
    }


def run_mission(
    operation: str,
    target: Optional[str] = None,
    audit: Optional[AuditTrail] = None,
    artifact_dir: str = "docs/engineering/reports",
    repo: Optional[str] = None,
    approval_reason: str = "",
    findings: Optional[List[Dict[str, Any]]] = None,
    diagnosis: Optional["DiagnosisResult"] = None,
    ward_manager=None,
) -> Dict[str, Any]:
    """Satu dispatcher eksekusi — pilih eksekutor berdasarkan `operation`.

    Ini BUKAN executor kedua: setiap cabang memanggil connector canonical
    (RealExecutionHarness / m8 mission framework) yang sudah terbukti. HANYA
    operasi yang telah dibuka jalurnya yang dieksekusi; lainnya ->
    UnsupportedOperationError (jujur BLOCKED, 0 side effect).

    W1 (Ward Activation): untuk operasi environment.* dengan target yang BUKAN
    citizen (`local-machine` dll.), SAM me-resolve target sbg WARD eksternal dan
    melewati Ward boundary (tenant + status + entrustment + capability scope)
    SEBELUM adapter dipanggil. `ward_manager` = composition root Ward (optional;
    default = global get_ward_manager()). Bila ward_manager tak tersedia ATAU
    target bukan citizen tapi tak terresolve sbg Ward -> refused (BLOCKED, 0
    mutation). local-machine tetap citizen (EnvironmentDiscovery), BUKAN Ward.

    Dibuka bertahap (aman dulu):
      - github.create_issue -> m8_002_build (PROVEN M8-006/M9)
      - web.open / web.get  -> RealBrowserConnector (read-only)
      - http.<endpoint>     -> RealHttpConnector (read-only)
      - environment.observe -> EnvironmentObservationAdapter (read-only, R1-002)
        ATAU OpenClawObservationAdapter (Ward, W1) bila target adalah Ward.
      - environment.investigate -> EnvironmentInvestigationAdapter (read-only, R1-003)
      - environment.diagnose -> EnvironmentDiagnosisAdapter (read-only, R1-004)
      - environment.recommend -> EnvironmentRecommendationAdapter (read-only, R1-005)
      - (email.send / db.write / process.run) -> BELUM dibuka -> BLOCKED
    """
    op = (operation or "").strip()
    if op.startswith("github."):
        REPO = repo or target or DEFAULT_TEST_REPO
        return run_github_real_mission(repo=REPO, audit=audit, artifact_dir=artifact_dir)
    if op.startswith("environment."):
        subject_id = (target or "").strip() or "local-machine"
        # W1: Ward resolution utk target non-citizen (mis. OpenClaw).
        ward_result = _maybe_resolve_ward(subject_id, op, ward_manager)
        if ward_result is not None:
            return ward_result
        # target citizen (local-machine dll.) -> jalur environment existing.
        if op.startswith("environment.investigate"):
            return run_environment_investigation_mission(subject_id=subject_id)
        if op.startswith("environment.diagnose"):
            return run_environment_diagnosis_mission(findings=findings,
                                                     subject_id=subject_id)
        if op.startswith("environment.recommend"):
            return run_environment_recommendation_mission(diagnosis=diagnosis,
                                                          subject_id=subject_id)
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
                                "environment.observe", "environment.investigate",
                                "environment.diagnose", "environment.recommend",
                                "execute", "act")
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
        "environment.investigate": "investigasi environment",
        "environment.diagnose": "diagnosis environment",
        "environment.recommend": "rekomendasi environment",
    }.get(conn, "eksekusi")
    _blocked_msg = {
        "github_api": ("GitHub tidak dapat digunakan karena GITHUB_TOKEN tidak "
                        "tersedia atau GITHUB_TEST_REPO kosong."),
        "web.fetch": "Membaca halaman web terblokir (network/driver tidak tersedia).",
        "http.get": "Panggilan HTTP terblokir (endpoint/kredensial).",
        "environment.observe": "Observasi environment terblokir (probe tidak menghasilkan entitas).",
        "environment.investigate": "Investigasi environment terblokir (probe tidak menghasilkan entitas).",
        "environment.diagnose": "Diagnosis environment terblokir (tidak ada evidence untuk dinilai).",
        "environment.recommend": "Rekomendasi environment terblokir (tidak ada diagnosis untuk dinilai).",
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
