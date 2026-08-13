"""service.py — MissionUXService (M9-001..006).

SATU pintu yang dipakai UI. Application service TIPIS, TIDAK punya authority.
Aturan:
  - Tidak buat executor kedua (mission dijalankan lewat runner.py -> m8_002_build).
  - Tidak pegang secret. Kredensial hanya lewat SecretProvider env ke
    CredentialBoundary (sudah PROVEN M8-005).
  - Tidak evaluasi policy. Serah ApprovalGate canonical.
  - State observable via UxMissionState (request -> understanding -> plan ->
    approval -> result -> evidence -> audit), failure semantics: BLOCKED /
    FAILED / REJECTED / COMPLETED.
  - Untuk vertical slice ini, recognition memahami pola "github create issue"
    sederhana (regex kata kunci) — bukan AI perencana; planning yang lebih
    kaya akan ditambah saat diintegrasikan dengan MCR.
"""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sam.application.ux.approval import (
    ApprovalCoordinator,
    ApprovalDecisionIntent,
    ApprovalRequest,
    ApprovalStatus,
)
from sam.application.ux.mission_request import MissionRequest, MissionRequestStatus
from sam.application.ux.plan import MissionPlan, MissionPlanStatus
from sam.application.ux.runner import (
    UnsupportedOperationError,
    classify_mission_outcome,
    run_mission,
)
from sam.application.ux.state import UxMissionState, UxFailureKind, UxStateStatus
from sam.application.ux.store import MissionStore
# M11-002: backend persistent opsional. Bila env SAM_PG_DSN diset, service
# otomatis memakai PostgresMissionStore (plugin) — JSON tetap default. Semua
# via API yang sama (load/save/enable/clear), jadi jalur & test lama tidak berubah.
try:
    from sam.application.ux.pgstore import PostgresMissionStore
    _HAS_PG = True
except Exception:  # pragma: no cover - psycopg2 tidak terpasang
    _HAS_PG = False
# M12-001: Repository Pattern — persistence per-entity opsional. Bila ada
# `persistence` (PersistenceUnit), state/source-of-truth ditulis per-entity ke
# repository (per mission_id) agar multi-mission & survive restart. Default:
# tanpa persistence -> perilaku in-memory/JSON lama (regresi M10 aman).
try:  # pragma: no cover - import opsional bila jalur repo tidak tersedia
    from sam.application.ux.persistence import build_persistence_unit
    from sam.application.ux import repositories as _repositories
    _HAS_REPO = True
except Exception:  # pragma: no cover
    _HAS_REPO = False


# Repo test default untuk GitHub mutation (repo TEST, bukan production).
DEFAULT_TEST_REPO = "VanM-Hub/test-issues"


def _blocked_state(reason: str) -> "UxMissionState":
    """Buat UxMissionState berstatus BLOCKED (M12-004/005 fail-closed).
    Dipakai saat produksi tidak siap (PG down / tidak ada persistence yang
    sah), agar operasi baru TIDAK berjalan & state menunjukkan alasan jelas."""
    st = UxMissionState()
    st.status = str(UxStateStatus.BLOCKED)
    st.failure_kind = "persistence-required"
    st.failure_message = reason
    st.approval_status = "blocked"
    return st


class MissionUXService:
    """Product entry point untuk UI. In-memory per-request store."""

    def __init__(
        self,
        test_repo: str = DEFAULT_TEST_REPO,
        artifact_dir: str = "docs/engineering/reports",
        store: Optional["MissionStore"] = None,
        persistence: Optional["object"] = None,
    ) -> None:
        self._test_repo = test_repo or DEFAULT_TEST_REPO
        self._artifact_dir = artifact_dir
        self._request: Optional[MissionRequest] = None
        self._plan: Optional[MissionPlan] = None
        self._approval = ApprovalCoordinator()
        self._state: Optional[UxMissionState] = None
        self._last_result: Optional[Dict[str, Any]] = None
        self._audit: List[Dict[str, Any]] = []
        # M12-001: PersistenceUnit opsional (Repository Pattern). Bila diberikan
        # (atau env PG/produksi dikonfigurasi), state ditulis per-entity ke repo.
        # M12-004/005: produksi (SAM_ENV=production) WAJIB PG ready; bila tidak
        # siap -> fail-closed (BLOCKED, tanpa fallback diam-diam ke in-memory).
        self._production_blocked = False
        self._persistence = getattr(self, "_persistence", None)
        if persistence is not None:
            self._persistence = persistence
        elif _HAS_REPO:
            _unit, _info = build_persistence_unit()
            if _info.get("production"):
                if not _info.get("ready", True):
                    # Produksi fail-closed: PG tidak siap -> jangan fallback.
                    self._persistence = None
                    self._production_blocked = True
                    if getattr(self, "_state", None) is None:
                        self._state = _blocked_state(_info.get("reason", "persistence unavailable"))
                else:
                    self._persistence = _unit
        # M10-007: persistensi — restart TIDAK menghilangkan operational truth.
        # M11-002: bila SAM_PG_DSN diset (produksi), pakai PostgreSQL; selain itu JSON.
        # M12-005: saat produksi fail-closed (PG down), JANGAN mencoba konek ke PG
        # utk _store snapshot — pakai store in-memory KOSONG (operasi tetap diblokir
        # oleh guard di atas; tidak ada fallback diam-diam untuk truth).
        if store is not None:
            self._store = store
        elif self._production_blocked:
            self._store = MissionStore()
        elif _HAS_PG and os.environ.get("SAM_PG_DSN"):
            self._store = PostgresMissionStore(dsn=os.environ["SAM_PG_DSN"]).enable()
        else:
            self._store = MissionStore()
        self._idem: Dict[str, Dict[str, Any]] = {}  # {key: {request_id, text}}
        self._repo_recovered = False  # M12-003: repo jadi source truth audit/idem
        self._recover_from_store()

    # ------------------------------------------------------------------
    # M10-007 — persistence/recovery: restart TIDAK menghilangkan truth.
    # ------------------------------------------------------------------
    def _recover_from_store(self) -> None:
        """Restore state mission terakhir dari disk (recovery setelah restart).
        Membangun kembali UxMissionState dari dict yang dipersist. Dipanggil
        dalam __init__; saling toleran bila file belum ada / korup."""
        # M12-001: bila ada PersistenceUnit, coba pulihkan dari repository
        # per-entity (source of truth = PG/multi-mission).
        if self._persistence is not None:
            try:
                self._recover_from_repository()
            except Exception:  # pragma: no cover
                self._state = None
                self._audit = []
            if self._state is not None:
                return
        data = self._store.load()
        if not data:
            return
        state_dict = data.get("state")
        if not state_dict:
            return
        try:
            st = UxMissionState()
            st.request_id = state_dict.get("request_id", "")
            st.request_text = state_dict.get("request", "")
            st.what_sam_understood = (state_dict.get("understanding") or {}).get(
                "what_sam_understood", "")
            st.operation = (state_dict.get("understanding") or {}).get("operation", "")
            st.target = (state_dict.get("understanding") or {}).get("target", "")
            plan = state_dict.get("plan") or {}
            st.planned_steps = list(plan.get("planned_steps", []))
            st.approval_required = bool(plan.get("approval_required"))
            st.action_summary = plan.get("action_summary", "")
            appr = state_dict.get("approval") or {}
            st.approval_status = appr.get("status", "")
            st.approval_decision = appr.get("decision")
            ex = state_dict.get("execution") or {}
            st.status = ex.get("status", "")
            st.failure_kind = ex.get("failure_kind", "")
            st.failure_message = ex.get("failure_message", "")
            st.result_summary = ex.get("result_summary", "")
            st.evidence = list(state_dict.get("evidence", []))
            st.artifact_ref = state_dict.get("artifact_ref", "")
            st.audit_ref = state_dict.get("audit_ref", "")
            st.timeline = list(state_dict.get("timeline", []))
            st.observability = dict(state_dict.get("observability", {}) or {})
            st.updated_at = state_dict.get("updated_at", st.updated_at)
            self._state = st
        except Exception:
            # File korup / versi lama -> mulai bersih, truth tetap aman (0 aksi).
            self._state = None
        # Restore audit trail (sanitized).
        # Restore audit trail (sanitized). Hanya dari JSON bila repo TIDAK
        # menjadi sumber (M12-003: repo lebih baru & benar).
        if not self._repo_recovered:
            self._audit = [dict(e) for e in (data.get("audit") or [])]
            # Restore idempotency map (request_id + text) utk cegah retry ganda.
            for k, v in (data.get("idem") or {}).items():
                self._idem[k] = dict(v)

    def _persist(self) -> None:
        """Snapshot state mission + audit + idem ke disk (tanpa secret).
        Bila PersistenceUnit ada (M12-001), state juga ditulis per-entity ke
        repository per mission_id — sehingga multi-mission & survive restart."""
        if self._state is not None and self._persistence is not None:
            try:
                self._persist_entities()
            except Exception:  # pragma: no cover — jangan blokir jalur lama
                pass
        if self._state is None:
            return
        payload = {
            "version": 1,
            "state": self._state.as_dict(),
            "audit": self._audit,
            "idem": {
                k: {"request_id": v.get("request_id", ""), "text": v.get("text", "")}
                for k, v in self._idem.items()
            },
        }
        self._store.save(payload)

    # ----------------------------------------------------------------
    # M12-001 — per-entity persistence ke repository (bila PersistenceUnit ada)
    # ----------------------------------------------------------------
    def _persist_entities(self) -> None:
        """Tulis state mission + execution + approval + audit utk mission saat
        ini ke repository per-entity (per mission_id), sehingga mission dapat
        hidup bersamaan tanpa overwrite dan survive restart."""
        if self._state is None or self._persistence is None:
            return
        st = self._state
        mission_id = (st.observability or {}).get("mission_id") or st.request_id
        if not mission_id:
            mission_id = st.request_id or "mission-unknown"
        self._persistence.missions.save_mission(
            mission_id, st.as_dict(),
        )
        exec_id = (st.observability or {}).get("execution_id")
        if exec_id:
            self._persistence.executions.save_execution(
                exec_id,
                {
                    "mission_id": mission_id,
                    "status": st.status,
                    "failure_kind": st.failure_kind,
                    "request_id": st.request_id,
                    "updated_at": st.updated_at,
                },
            )
        # idempotency keys -> persistent (M12-002 base)
        for k, v in self._idem.items():
            self._persistence.idempotency.save_idempotency(
                k, {"request_id": v.get("request_id", ""), "text": v.get("text", "")},
                mission_id,
            )

    def _recover_from_repository(self) -> None:
        """Pulihkan state mission + audit + idempotency dari repository (per-entity).
        Mengambil mission terakhir yang tersimpan; tolerance bila belum ada.
        Audit & idempotency dipulihkan SECARA INDEPENDEN dari ada/tidaknya
        mission — sehingga keduanya survive restart walau mission kosong."""
        if self._persistence is None:
            return
        # Restore audit trail dari repository (selalu, terlepas dari mission)
        try:
            self._audit = self._persistence.audit.load_audit()
        except Exception:  # pragma: no cover
            self._audit = []
        # Restore idempotency map dari repository (M12-002 base; selalu)
        try:
            self._idem = {}
            for k in self._persistence.idempotency.list_keys():
                rec = self._persistence.idempotency.load_idempotency(k)
                if rec:
                    self._idem[k] = {"request_id": rec.get("request_id", ""), "text": rec.get("text", "")}
        except Exception:  # pragma: no cover
            self._idem = {}
        # Tandai: repo sudah jadi sumber audit & idempotency, agar JSON store
        # (fallback) TIDAK menimpanya di _recover_from_store.
        self._repo_recovered = True
        # Restore mission terakhir (bila ada)
        missions = self._persistence.missions.list_missions()
        if not missions:
            return
        last_id = missions[-1]
        state_dict = self._persistence.missions.load_mission(last_id)
        if not state_dict:
            return
        try:
            st = UxMissionState()
            st.request_id = state_dict.get("request_id", "")
            st.request_text = state_dict.get("request", "")
            st.what_sam_understood = (state_dict.get("understanding") or {}).get(
                "what_sam_understood", "")
            st.operation = (state_dict.get("understanding") or {}).get("operation", "")
            st.target = (state_dict.get("understanding") or {}).get("target", "")
            plan = state_dict.get("plan") or {}
            st.planned_steps = list(plan.get("planned_steps", []))
            st.approval_required = bool(plan.get("approval_required"))
            st.action_summary = plan.get("action_summary", "")
            appr = state_dict.get("approval") or {}
            st.approval_status = appr.get("status", "")
            st.approval_decision = appr.get("decision")
            ex = state_dict.get("execution") or {}
            st.status = ex.get("status", "")
            st.failure_kind = ex.get("failure_kind", "")
            st.failure_message = ex.get("failure_message", "")
            st.result_summary = ex.get("result_summary", "")
            st.evidence = list(state_dict.get("evidence", []))
            st.artifact_ref = state_dict.get("artifact_ref", "")
            st.audit_ref = state_dict.get("audit_ref", "")
            st.timeline = list(state_dict.get("timeline", []))
            st.observability = dict(state_dict.get("observability", {}) or {})
            st.updated_at = state_dict.get("updated_at", st.updated_at)
            self._state = st
        except Exception:  # pragma: no cover
            self._state = None

    # ------------------------------------------------------------------
    # 1) submit — terima request manusia, SAM pahami, susun rencana, TARUH
    #    di WAITING_APPROVAL. Tidak ada eksekusi di sini.
    # ------------------------------------------------------------------
    def submit(self, text: str, idempotency_key: Optional[str] = None) -> UxMissionState:
        # M12-005: Fail-closed produksi — bila persistence PG tidak siap,
        # tolak mission baru (0 operasi, 0 side effect).
        if self._production_blocked:
            st = self._state if (self._state and self._state.status == str(UxStateStatus.BLOCKED)) \
                else _blocked_state("Fail-closed: persistence produksi tidak siap")
            self._state = st
            return st
        # M10-005: Idempotency-Key identical -> kembalikan state yg SAMA
        # (same logical operation), TIDAK membuat mission baru. Retry (mis.
        # karena network timeout) dengan key sama TIDAK menimbulkan operasi
        # ganda.
        if idempotency_key:
            existing = self._idem.get(idempotency_key)
            if existing is not None and self._state is not None:
                # Pastikan teks yang dipakai sama utk menghindari misuse key.
                if existing.get("text") == text:
                    return self._state
            # Key baru (atau teks berbeda) -> catat key utk operasi ini.
            self._idem[idempotency_key] = {"request_id": "", "text": text}

        # Pahami request terlebih dahulu (SAM memahami sebelum menyimpan).
        operation, target, understood, planned, action_summary, approval_reason = (
            self._interpret(text)
        )

        req = MissionRequest(
            request_id=f"req-{uuid.uuid4().hex[:8]}",
            text=text,
            operation=operation,
            target=target,
            status=MissionRequestStatus.UNDERSTOOD,
        )
        self._request = req
        if idempotency_key:
            self._idem[idempotency_key]["request_id"] = req.request_id

        plan = MissionPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            request_id=req.request_id,
            what_sam_understood=understood,
            planned_steps=planned,
            approval_required=bool(operation),
            approval_reason=approval_reason,
            status=MissionPlanStatus.PENDING_APPROVAL,
        )
        self._plan = plan

        # Pending approval (UI akan menampilkan [Approve][Reject]) — HANYA utk
        # operasi yang dikenali (M10-006: request invalid TIDAK boleh punya
        # jalur approval yang bisa dieksekusi).
        action = action_summary or f"SAM akan: {planned[0] if planned else 'melakukan tindakan'}"
        approval_req = ApprovalRequest(
            approval_id=f"apr-{uuid.uuid4().hex[:8]}",
            plan_id=plan.plan_id,
            request_id=req.request_id,
            action_summary=action,
            gates=[s for s in planned],
        )
        if operation:
            self._approval.record_pending(approval_req)

        _now = datetime.now(timezone.utc).isoformat()
        state = UxMissionState(
            request_id=req.request_id,
            request_text=req.text,
            what_sam_understood=understood,
            operation=operation,
            target=target,
            planned_steps=planned,
            approval_required=bool(operation),
            action_summary=action,
            approval_status=UxStateStatus.WAITING_APPROVAL,
            status=UxStateStatus.WAITING_APPROVAL,
        )
        # M10-003: observability sejak submit — misi, capability, target, waktu.
        state.observability = {
            "request_id": req.request_id,
            "mission_id": f"mission-{uuid.uuid4().hex[:12]}",
            "execution_id": "",
            "capability": operation or "none",
            "external_target": target or self._test_repo,
            "start_time": _now,
            "end_time": "",
            "status": UxStateStatus.WAITING_APPROVAL,
            "verification_result": "",
            "failure_reason": "",
            "approver": "",
        }
        self._state = state
        self._persist()
        return state

    # ------------------------------------------------------------------
    # 2) decide — user klik Approve/Reject (M9-003). Real gate.
    # ------------------------------------------------------------------
    def decide(self, intent: ApprovalDecisionIntent, approver: str = "user") -> UxMissionState:
        # M12-005: Fail-closed produksi — tolak keputusan bila persistence
        # produksi tidak siap (tidak boleh lanjut ke eksekusi).
        if self._production_blocked:
            st = self._state if (self._state and self._state.status == str(UxStateStatus.BLOCKED)) \
                else _blocked_state("Fail-closed: persistence produksi tidak siap")
            self._state = st
            return st
        if self._state is None or self._request is None or self._plan is None:
            raise RuntimeError("tidak ada mission yang sedang menunggu approval")

        # M10-006: request invalid (bukan capability) TIDAK boleh di-approve utk
        # dieksekusi. Approval hanya valid bila plan butuh approval (operation ada).
        if not self._state.approval_required or not self._request.operation:
            self._state.status = UxStateStatus.REJECTED
            self._state.failure_kind = UxFailureKind.REJECTED
            self._state.failure_message = (
                "Capability tidak dikenali — tidak ada operasi untuk dijalankan."
            )
            # TIDAK pernah memanggil executor. 0 side effect.
            obs = dict(self._state.observability or {})
            obs.update({"status": UxStateStatus.REJECTED,
                        "failure_reason": "invalid capability (denied)"})
            self._state.observability = obs
            self._audit.append({
                "stage": "approval",
                "event": "denied_invalid_capability",
                "ok": False,
                "blocked": True,
                "detail": "Capability tidak dikenali — eksekusi ditolak (0 mutation)",
            })
            self._persist()
            return self._state

        outcome = self._approval.decide(intent, approver=approver)
        state = self._state

        if outcome.status == ApprovalStatus.REJECTED:
            # User reject -> REJECTED, eksekusi TIDAK pernah berjalan.
            state.approval_status = UxStateStatus.REJECTED
            state.status = UxStateStatus.REJECTED
            state.failure_kind = UxFailureKind.REJECTED
            state.failure_message = "Mission ditolak oleh pengguna — tidak ada eksekusi."
            state.approval_decision = outcome.as_dict()
            # M10-003: observability lengkap untuk keputusan reject.
            obs = dict(state.observability or {})
            # Approver user yang sesungguhnya (gate set kosong saat reject).
            _approver = approver or "user"
            obs.update({
                "status": UxStateStatus.REJECTED,
                "end_time": datetime.now(timezone.utc).isoformat(),
                "verification_result": "none (ditolak, 0 mutation)",
                "failure_reason": "rejected oleh approver",
                "approver": _approver,
            })
            state.observability = obs
            # M9-004: audit terekam untuk SEMUA keputusan, termasuk reject.
            self._audit.append({
                "stage": "approval",
                "event": "rejected",
                "ok": True,
                "blocked": True,
                "detail": "Approval ditolak user — tanpa eksekusi (0 mutation)",
                "approver": _approver,
            })
            self._persist()
            return state

        # outcome == APPROVED -> jalankan mission nyata via jalur canonical.
        state.approval_status = UxStateStatus.APPROVED
        state.approval_decision = outcome.as_dict()
        state.status = UxStateStatus.RUNNING

        _exec_id = f"exec-{uuid.uuid4().hex[:12]}"
        obs = dict(state.observability or {})
        obs.update({
            "status": UxStateStatus.RUNNING,
            "execution_id": _exec_id,
            "approver": (outcome.as_dict().get("approver") or approver or "user"),
        })
        state.observability = obs

        operation = (self._request.operation or "").strip()
        repo = self._request.target or self._test_repo
        try:
            # Dispatcher eksekusi (B1/B2): pilih jalur canonical sesuai operasi.
            # GitHub -> m8_002_build (blok existing di bawah). web.*/http.* ->
            # connector read-only. Operasi lain -> UnsupportedOperationError
            # (BLOCKED jujur, 0 side effect).
            result = run_mission(
                operation=operation,
                target=self._request.target,
                repo=repo,
                artifact_dir=self._artifact_dir,
                approval_reason=f"APPROVED by {approver or 'user'}",
            )
        except UnsupportedOperationError as exc:
            state.status = UxStateStatus.BLOCKED
            state.failure_kind = UxFailureKind.BLOCKED
            state.failure_message = str(exc)
            obsb = dict(state.observability or {})
            obsb.update({
                "status": UxStateStatus.BLOCKED,
                "end_time": datetime.now(timezone.utc).isoformat(),
                "verification_result": "none (unsupported - 0 side effect)",
                "failure_reason": str(exc),
            })
            state.observability = obsb
            self._audit.append({
                "stage": "execute", "event": "unsupported_operation",
                "ok": False, "blocked": True, "detail": str(exc),
            })
            self._persist()
            return state
        except Exception as exc:  # noqa: BLE001 — interface harus tetap hidup
            state.status = UxStateStatus.FAILED
            state.failure_kind = UxFailureKind.FAILED
            state.failure_message = f"mission gagal: {exc}"
            obs2 = dict(state.observability or {})
            obs2.update({
                "status": UxStateStatus.FAILED,
                "end_time": datetime.now(timezone.utc).isoformat(),
                "verification_result": "none (gagal di eksekusi)",
                "failure_reason": str(exc),
            })
            state.observability = obs2
            self._audit.append({
                "stage": "execute", "event": "mission_failed",
                "ok": False, "blocked": False, "detail": str(exc),
            })
            self._persist()
            return state

        self._last_result = result
        verdict = classify_mission_outcome(result)

        state.status = (
            UxStateStatus.COMPLETED
            if verdict["status"] == "completed"
            else UxStateStatus.BLOCKED
            if verdict["status"] == "blocked"
            else UxStateStatus.FAILED
        )
        state.failure_kind = verdict["failure_kind"] or UxFailureKind.NONE
        state.failure_message = (
            "" if verdict["status"] == "completed" else verdict["message"]
        )
        state.result_summary = result.get("title", "") + (
            " (ok)" if result.get("ok") else " (gagal)"
        )

        # M10-003: observability final setelah eksekusi (tanpa secret).
        gh_verify = next(
            (t for t in (result.get("timeline") or []) if t.get("stage") == "verify"),
            None,
        )
        obs3 = dict(state.observability or {})
        obs3.update({
            "status": state.status,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "verification_result": (
                (gh_verify or {}).get("detail")
                or ("ok (evidence eksternal)" if state.status == UxStateStatus.COMPLETED
                    else verdict["message"])
            ),
            "failure_reason": verdict["message"]
            if state.status in (UxStateStatus.BLOCKED, UxStateStatus.FAILED)
            else "",
        })
        state.observability = obs3

        # Evidence chain runut (M9-004).
        timeline = result.get("timeline", []) or []
        state.timeline = [
            {"stage": t.get("stage"), "ok": t.get("ok"), "blocked": t.get("blocked"),
             "detail": t.get("detail", "")}
            for t in timeline
        ]
        # Untuk "what actually happened" (M9-002) — tampilkan issue_url jika ada
        # (nilai dari `scrubbed` boundary; `masked`/secret TIDAK pernah diambil).
        gh = next(
            (t for t in timeline if t.get("stage") in ("github_api", "execute", "act")
             and t.get("scrubbed")),
            None,
        )
        scrubbed = (gh or {}).get("scrubbed") or {}
        if scrubbed.get("ok"):
            state.evidence = [{
                "kind": "external_github_issue",
                "url": scrubbed.get("issue_url", ""),
                "number": scrubbed.get("number"),
                "detail": scrubbed.get("detail", ""),
            }]
        elif result.get("target") and not scrubbed:
            # Non-GitHub (web.*/http.*): rekam target hasil eksekusi sbg evidence
            # read-only (tanpa secret).
            state.evidence = [{
                "kind": "read_only_result",
                "target": result.get("target", ""),
                "detail": result.get("detail", ""),
            }]
        state.artifact_ref = result.get("artifact_path", "")
        state.audit_ref = f"audit_count={result.get('audit_count', 0)}"
        # M9-004: append mission timeline ke audit trail (sanitized, no secret).
        for t in (result.get("timeline") or []):
            self._audit.append({
                "stage": t.get("stage"),
                "ok": t.get("ok"),
                "blocked": t.get("blocked"),
                "detail": t.get("detail", ""),
            })
        self._persist()
        return state

    # ------------------------------------------------------------------
    # 3) get_state — ViewModel saat ini untuk UI.
    # ------------------------------------------------------------------
    def get_state(self) -> Optional[UxMissionState]:
        return self._state

    # ------------------------------------------------------------------
    # 4) get_evidence / get_audit — detail untuk operator.
    # ------------------------------------------------------------------
    def get_evidence(self) -> List[Dict[str, Any]]:
        return list(self._state.evidence) if self._state else []

    def get_audit(self) -> List[Dict[str, Any]]:
        # M9-004: audit trail runut untuk SEMUA keputusan (approve & reject),
        # sanitized — tidak pernah memuat secret.
        return list(self._audit)

    # ------------------------------------------------------------------
    # internal: interpret request jadi rencana sederhana (vertical slice)
    # ------------------------------------------------------------------
    @staticmethod
    def _interpret(text: str) -> Tuple[str, str, str, List[str], str, str]:
        """Deteksi operasi dari teks.

        Mencoba pemahaman via AI lokal (Gemma/Ollama) dulu; bila Ollama tidak
        tersedia / gagal / offline -> fallback ke pola regex (mode offline).

        Returns: (operation, target, understood, planned_steps, action_summary, reason)
        operation "" -> tidak dikenali, tidak ada eksekusi direncanakan.
        """
        t = (text or "").strip()
        low = t.lower()

        # 1) Coba pemahaman cerdas via AI lokal (Gemma3:1b via Ollama).
        #    Menutup kesenjangan "SAM hanya kenal pola kata" -> SAM bisa
        #    memahami permintaan bahasa bebas. Fallback aman bila offline.
        attempt = MissionUXService._interpret_via_ai(t)
        if attempt is not None and attempt[0]:
            return attempt

        # Fallback: pola regex (mode offline / Ollama tidak tersedia).
        is_github_issue = bool(
            re.search(r"github", low)
            and re.search(r"(issue|masalah|tiket|new issue|create)", low)
        )

        if is_github_issue:
            operation = "github.create_issue"
            target = os.environ.get("GITHUB_TEST_REPO") or DEFAULT_TEST_REPO
            title_match = re.search(r'(?:judul|title)\s*[:=]\s*"?([^"\n]+)"?', t, flags=re.I)
            if title_match:
                title = title_match.group(1).strip()
                body = re.sub(title_match.group(0), "", t, count=1).strip()
            else:
                title = t
                body = t
            understood = (
                f"SAM memahami: membuat GitHub issue di repo '{target}'."
            )
            planned = [
                "memverifikasi koneksi GitHub (boundary)",
                f"membuat issue di repo '{target}' dengan judul dari permintaan",
                "melakukan verifikasi independen (GET issue dari GitHub)",
            ]
            action_summary = (
                f"SAM akan membuat GitHub issue di repo '{target}'."
            )
            approval_reason = (
                "Tindakan ini menghasilkan efek eksternal nyata pada GitHub "
                "(repo uji). Persetujuan Anda diperlukan sebelum eksekusi."
            )
            return (
                operation, target, understood, planned, action_summary, approval_reason
            )

        # Fallback web (read-only): "buka website X" / "buka <url>".
        # Tangkap URL eksplisit atau domain, agar target eksekusi benar.
        url_match = re.search(
            r"(https?://[^\s]+|www\.[^\s]+|[a-z0-9-]+\.[a-z]{2,}(?:/[^\s]*)?)",
            t, flags=re.I,
        )
        is_web = bool(re.search(r"(buka|brows|open|web|website|site|halaman)", low))
        if is_web:
            operation = "web.open"
            raw_url = (url_match.group(1) if url_match else "") or ""
            target = raw_url if raw_url.startswith("http") else f"https://{raw_url}" if raw_url else ""
            if not target:
                # Tidak ada URL/domain yang ditangkap -> tidak bisa dieksekusi.
                return (
                    "", "", "SAM tidak menemukan URL untuk dibuka pada permintaan ini.",
                    [], "", "",
                )
            understood = f"SAM memahami: membuka halaman web '{target}' (read-only)."
            planned = [
                "memverifikasi konektivitas (online check)",
                f"mengambil konten halaman web '{target}'",
                "melaporkan hasil baca (tanpa mengubah apapun)",
            ]
            action_summary = f"SAM akan membuka dan membaca halaman web '{target}' (read-only)."
            approval_reason = (
                "Operasi ini read-only (membaca halaman web) — tidak mengubah state "
                "eksternal, namun tetap disediakan persetujuan Anda untuk transparansi."
            )
            return (
                operation, target, understood, planned, action_summary, approval_reason
            )

        return (
            "",
            "",
            "SAM tidak mengenali operasi pada permintaan ini.",
            [],
            "",
            "",
        )

    # ------------------------------------------------------------------
    # pemahaman cerdas via AI lokal (Gemma3:1b / Ollama) — tanpa internet
    # ------------------------------------------------------------------
    _AI_CAPABILITIES = (
        "Operasi SAM yang diketahui: "
        "[github.create_issue] buat/tingkat issue GitHub; "
        "[email.send] kirim email; "
        "[web.open] buka/baca halaman web; "
        "[http.call] panggil API/HTTP eksternal; "
        "[ai.think] minta AI berpikir/menjawab; "
        "[db.query] baca/tulis database; "
        "[process.run] jalankan perintah/command lokal."
    )

    @staticmethod
    def _interpret_via_ai(text: str) -> Optional[Tuple[str, str, str, List[str], str, str]]:
        """Pahami permintaan via Gemma3:1b (Ollama lokal, no internet).

        Menghasilkan JSON terstruktur. Bila Ollama tidak tersedia / timeout /
        hasil tidak valid -> kembalikan None (caller fallback ke regex).
        Aman offline: tidak ada side effect bila gagal.
        """
        if not text.strip():
            return None
        try:
            from sam.providers.execution.provider_executor import (
                ProviderExecutor,
                ProviderUnavailableError,
            )
            executor = ProviderExecutor()
            prompt = (
                f"{MissionUXService._AI_CAPABILITIES}\n\n"
                "Instruksi: Dari permintaan berikut, tentukan operasi SAM yang paling "
                "cocok (di antara daftar di atas). Jika tidak cocok sama sekali, pakai "
                "operation kosong. Jawab HANYA dengan JSON valid tanpa teks lain, format:\n"
                '{"operation": "<salah satu operation atau \"\">", '
                '"target": "<objek sasaran, atau kosong>", '
                '"understood": "<kalimat singkat apa yang SAM pahami>", '
                '"planned": ["<langkah 1>", "<langkah 2>"]}\n\n'
                f"Permintaan: {text}"
            )
            raw = executor.execute(
                "ollama",
                "chat",
                {"prompt": prompt, "model": "gemma3:1b", "max_tokens": 256},
                timeout_seconds=90,
            )
            content = MissionUXService._extract_ai_text(raw)
            parsed = MissionUXService._parse_ai_json(content)
            if not parsed:
                return None
            operation = str(parsed.get("operation") or "")
            if not operation:
                return None  # belum operasi yang dikenali -> biarkan fallback/tolak
            target = str(parsed.get("target") or "") or os.environ.get(
                "GITHUB_TEST_REPO") or DEFAULT_TEST_REPO
            understood = str(parsed.get("understood") or "")
            # Normalisasi: selalu awali "SAM memahami:" agar konsisten dengan
            # mode regex & harapan UI (jangan ubah kalau sudah ada).
            understood = understood.strip()
            if understood and not understood.startswith("SAM memahami"):
                understood = f"SAM memahami: {understood}"
            elif not understood:
                understood = (f"SAM memahami: menjalankan operasi '{operation}'.")
            planned_raw = parsed.get("planned") or []
            planned = [str(x) for x in planned_raw if str(x)] or [
                "melakukan operasi {}".format(operation)
            ]
            action_summary = f"SAM akan menjalankan operasi '{operation}'"
            if target:
                action_summary += f" pada '{target}'"
            reason = (
                "Pemahaman dihasilkan AI lokal (Gemma3:1b). Tindakan ini dapat "
                "menghasilkan efek eksternal; persetujuan Anda diperlukan."
            )
            return (operation, target, understood, planned, action_summary, reason)
        except (ProviderUnavailableError, Exception):  # noqa: BLE001
            return None

    @staticmethod
    def _extract_ai_text(raw: Dict[str, Any]) -> str:
        """Ekstrak teks dari respons ProviderExecutor (ollama OpenAI-compatible)."""
        try:
            payload = raw.get("payload") or {}
            cand = payload.get("raw") or raw
            choices = cand.get("choices") or []
            if choices:
                msg = choices[0].get("message") or {}
                return str(msg.get("content") or "")
            content = cand.get("content")
            if content is not None:
                return str(content)
        except Exception:  # noqa: BLE001
            pass
        return str(raw)

    @staticmethod
    def _parse_ai_json(content: str) -> Optional[Dict[str, Any]]:
        """Parse JSON dari output model; toleran kutipan salah / teks tambahan."""
        import json as _json
        if not content:
            return None
        try:
            d = _json.loads(content)
            if isinstance(d, dict):
                return d
        except Exception:  # noqa: BLE001
            pass
        try:
            start = content.find("{")
            end = content.rfind("}")
            if 0 <= start < end:
                d = _json.loads(content[start:end + 1])
                if isinstance(d, dict):
                    return d
        except Exception:  # noqa: BLE001
            pass
        return None
