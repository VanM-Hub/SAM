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
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sam.application.ux.approval import (
    ApprovalCoordinator,
    ApprovalDecisionIntent,
    ApprovalRequest,
    ApprovalStatus,
)

if TYPE_CHECKING:  # pragma: no cover - hanya utk anotasi tipe
    from sam.ward.capability.contracts import DiagnosisResult
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

    _HAS_REPO = True
except Exception:  # pragma: no cover
    _HAS_REPO = False

# M12-008: Observability — telemetri nyata (counter) diekspos via /metrics.
from sam.application.ux.metrics import metrics as _metrics  # type: ignore


# Repo test default untuk GitHub mutation (repo TEST, bukan production).
DEFAULT_TEST_REPO = "VanM-Hub/test-issues"


def _build_ward_manager_for_tenant(approver: Optional[str] = None):
    """W1: Bangun WardManager terikat tenant (reuse AD-ENG-006 identity).

    Memakai composition root Ward (get_ward_manager) dan mengikat tenant aktif
    = {username: approver, role: operator}. Ownership entrustment Ward dicocokkan
    terhadap username ini (cross-tenant -> fail-closed). Bila Ward subsystem
    tak tersedia -> None (jalur citizen existing tidak berubah).
    """
    try:
        from sam.ward.wiring import get_ward_manager
        mgr = get_ward_manager()
        if mgr is None:
            return None
        return mgr.with_tenant({
            "username": (approver or "user").strip() or "user",
            "role": "operator",
        })
    except Exception:  # noqa: BLE001 - Ward belum tersedia -> None (citizen path)
        return None

# Kosakata DOMAIN environment (SATU SUMBER): target sistem + kondisi observable.
# Ini bukan template kalimat, melainkan kosakata domain yang dipakai konsisten oleh
# (a) guard CHAT untuk MEMBIARKAN frasa diagnosa sistem lolos ke resolver, dan
# (b) operation resolver (_interpret_environment_investigate) sebagai authority.
# Prinsip (Van 2026-08-16): wh-question != CHAT; pisahkan contextual/explanatory
# question (CHAT) dari system/environment diagnostic question (environment.investigate)
# berdasar SEMANTIC INTENT (ada target sistem + kondisi), bukan awalan kalimat.
_ENV_SYSTEM_TARGETS = re.compile(
    r"\b(komputer|pc|mesin|host|sistem|system|environment|env|lokal|local|"
    r"cpu|prosesor|process|proc|ram|memory|disk|storage|port|network|jaringan|wifi|baterai|battery)\b",
    re.IGNORECASE,
)
_ENV_OBSERVABLE_CONDITIONS = re.compile(
    r"\b(lambat|lelet|macet|hang|berat|sering|lambat|lag|lemot|tinggi|tinggal|penuh|habis|gagal|error|bermasalah|tidak\s+bisa|nggak\s+bisa)\b",
    re.IGNORECASE,
)
# Kata kerja perintah: bila frasa memuat ini, TETAP mission (bukan CHAT).
_CMD_VERBS = re.compile(
    r"\b(buat|jalankan|jalani|lakukan|restart|reboot|kirim|periksa|scan|diagnos|simulasikan|hapus|install|uninstall|buka|tutup|eksekusi|execute|run|stop|start|investiga|selidik)\b",
    re.IGNORECASE,
)


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
        # R1-004 W1: cache findings investigasi terakhir (environment.investigate)
        # agar misi diagnosis terpisah dapat menilai evidence tanpa investigate ulang.
        self._last_investigation_findings: Optional[List[Dict[str, Any]]] = None
        # R1-005: cache DiagnosisResult CANONICAL terakhir (dari environment.diagnose)
        # agar misi recommendation berikutnya makan dari diagnosis terakhir.
        # BUKAN Dict serialized — application boundary memegang canonical domain
        # result (keputusan final Van rev.2). Serialization (bila dibutuhkan)
        # dilakukan di boundary persistence, bukan di tengah application flow.
        self._last_diagnosis_result: Optional["DiagnosisResult"] = None
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
                "what_sam_understood", ""
            )
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
                _metrics.inc("sam_persistence_error")
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
            mission_id,
            st.as_dict(),
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
                k,
                {"request_id": v.get("request_id", ""), "text": v.get("text", "")},
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
                    self._idem[k] = {
                        "request_id": rec.get("request_id", ""),
                        "text": rec.get("text", ""),
                    }
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
                "what_sam_understood", ""
            )
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
            _metrics.inc("sam_mission_blocked")
            st = (
                self._state
                if (self._state and self._state.status == str(UxStateStatus.BLOCKED))
                else _blocked_state("Fail-closed: persistence produksi tidak siap")
            )
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
                    _metrics.inc("sam_idempotency_replay")
                    return self._state
                _metrics.inc("sam_idempotency_conflict")
            # Key baru (atau teks berbeda) -> catat key utk operasi ini.
            self._idem[idempotency_key] = {"request_id": "", "text": text}

        _metrics.inc("sam_mission_received")

        # Pahami request terlebih dahulu (SAM memahami sebelum menyimpan).
        operation, target, understood, planned, action_summary, approval_reason, resolve_reason = (
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

        # Model canonical CHAT vs MISSION (boundary audit 2026-08-16, Aster + Van):
        #   operation == ""      -> CHAT (bukan Mission, tidak ada approval)
        #   operation != ""     -> MISSION (terlepas dari approval)
        #       read-only       -> MISSION tanpa approval (observe/investigate/
        #                           diagnose/recommend — tidak mengubah state eksternal)
        #       mutating        -> MISSION + approval (github.create_issue dsb)
        # approval_required adalah SINYAL TERPISAH dari ke-mission-an, bukan sinonim
        # "apakah ini mission". M10-006 tetap berlaku: approval HANYA dijalankan utk
        # operasi yang butuh approval (request invalid tetap tanpa jalur eksekusi).
        # Ke-mission-an = operation != ""; approval adalah sinyal terpisah.
        # ADR-007 (FAIL-CLOSED INVARIANT di pintu Mission): setiap operation yang
        # sampai di sini WAJIB lolos exact canonical capability set. Bind LLM =
        # candidate, SAM validator = authority (deterministic). Memastikan C1
        # terlepas dari jalur operation (LLM/regex/mock): operation non-admissible
        # -> dipaksa "" (no Mission), alasan ditangkap utk observability.
        if operation:
            _resolved, _reason_11 = MissionUXService._resolve_capability(operation)
            if _resolved is None:
                resolve_reason = _reason_11 if resolve_reason is None else resolve_reason
                operation = ""
                target = ""
                planned = []
                understood = (
                    "SAM tidak dapat memetakan operasi ke capability SAM yang "
                    "sudah terbukti. Tidak ada operasi yang akan dijalankan."
                )
                action_summary = ""
                approval_reason = ""
        approval_required = bool(operation) and not self._operation_is_read_only(operation)
        # status internal pasca-submit (sebelum keputusan/eksekusi):
        #   CHAT / MISSION read-only -> UNDERSTOOD (SAM paham, tidak menunggu approval)
        #   MISSION mutating         -> WAITING_APPROVAL (menunggu keputusan user)
        _pending = UxStateStatus.WAITING_APPROVAL if approval_required else UxStateStatus.UNDERSTOOD

        plan = MissionPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            request_id=req.request_id,
            what_sam_understood=understood,
            planned_steps=planned,
            approval_required=approval_required,
            approval_reason=approval_reason,
            # DRAFT = Mission dibentuk tapi tidak menunggu approval (candidate/
            # read-only); PENDING_APPROVAL = menunggu keputusan user. Grounding
            # ulang MissionPlanStatus yang sudah ada (bukan state machine baru).
            status=(
                MissionPlanStatus.PENDING_APPROVAL if approval_required else MissionPlanStatus.DRAFT
            ),
        )
        self._plan = plan

        # Pending approval (UI akan menampilkan [Approve][Reject]) — HANYA utk
        # operasi yang BUTUH approval (M10-006: request invalid / read-only TIDAK
        # boleh punya jalur approval yang bisa dieksekusi utk mengubah state).
        action = action_summary or f"SAM akan: {planned[0] if planned else 'melakukan tindakan'}"
        approval_req = ApprovalRequest(
            approval_id=f"apr-{uuid.uuid4().hex[:8]}",
            plan_id=plan.plan_id,
            request_id=req.request_id,
            action_summary=action,
            gates=[s for s in planned],
        )
        if approval_required:
            self._approval.record_pending(approval_req)

        _now = datetime.now(timezone.utc).isoformat()
        state = UxMissionState(
            request_id=req.request_id,
            request_text=req.text,
            what_sam_understood=understood,
            operation=operation,
            target=target,
            planned_steps=planned,
            approval_required=approval_required,
            action_summary=action,
            approval_status=(
                UxStateStatus.WAITING_APPROVAL if approval_required else UxStateStatus.NONE
            ),
            status=_pending,
        )
        # M10-003: observability sejak submit — misi, capability, target, waktu.
        # ADR-007: untuk invalid/unresolved (operation kosong akibat candidate
        # LLM tak-admissible), simpan resolution + resolve_reason sbg diagnostic/
        # trace (audit/debug) — TANPA merubah domain lifecycle jadi state baru.
        #   resolution="chat"     -> percakapan biasa (halo, terima kasih, dll)
        #   resolution="invalid"  -> input tak-dapat-di-resolve ke capability
        if resolve_reason is not None:
            _resolution = "invalid"  # unresolved / candidate tak-admissible
        elif operation:
            _resolution = "valid"  # ter-resolve ke capability exact
        else:
            _resolution = "chat"  # percakapan biasa (guard deterministik)
        state.observability = {
            "request_id": req.request_id,
            "mission_id": f"mission-{uuid.uuid4().hex[:12]}",
            "execution_id": "",
            "capability": operation or "none",
            "external_target": target or self._test_repo,
            "start_time": _now,
            "end_time": "",
            "status": _pending,
            "verification_result": "",
            "failure_reason": "",
            "approver": "",
            "resolution": _resolution,
            "resolve_reason": resolve_reason,
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
            st = (
                self._state
                if (self._state and self._state.status == str(UxStateStatus.BLOCKED))
                else _blocked_state("Fail-closed: persistence produksi tidak siap")
            )
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
            obs.update(
                {"status": UxStateStatus.REJECTED, "failure_reason": "invalid capability (denied)"}
            )
            self._state.observability = obs
            self._audit.append(
                {
                    "stage": "approval",
                    "event": "denied_invalid_capability",
                    "ok": False,
                    "blocked": True,
                    "detail": "Capability tidak dikenali — eksekusi ditolak (0 mutation)",
                }
            )
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
            obs.update(
                {
                    "status": UxStateStatus.REJECTED,
                    "end_time": datetime.now(timezone.utc).isoformat(),
                    "verification_result": "none (ditolak, 0 mutation)",
                    "failure_reason": "rejected oleh approver",
                    "approver": _approver,
                }
            )
            state.observability = obs
            # M9-004: audit terekam untuk SEMUA keputusan, termasuk reject.
            self._audit.append(
                {
                    "stage": "approval",
                    "event": "rejected",
                    "ok": True,
                    "blocked": True,
                    "detail": "Approval ditolak user — tanpa eksekusi (0 mutation)",
                    "approver": _approver,
                }
            )
            _metrics.inc("sam_mission_rejected")
            self._persist()
            return state

        # outcome == APPROVED -> jalankan mission nyata via jalur canonical.
        _metrics.inc("sam_mission_approved")
        return self._execute_mission(
            approval_status=UxStateStatus.APPROVED,
            approval_decision=outcome.as_dict(),
            approver=approver,
        )

    def _execute_mission(self, *, approval_status, approval_decision, approver, ward_tenant=None) -> UxMissionState:
        """Jalankan mission via SATU execution boundary canonical (run_mission).

        Dipanggil oleh dua jalur yang TIDAK saling menggantikan:
          1) decide() APPROVED  (human approval nyata)  -> approval_status=APPROVED
          2) execute_policy_authorized() (read-only, tanpa human approval nyata,
             otorisasi dari policy capability)          -> approval_status=<honest>

        BUKAN execution path kedua: ini SATU-satunya tempat run_mission dipanggil
        dari service ini. Kedua jalur melewati boundary yang sama -> evidence +
        verification + audit identik. TIDAK ada fake approval: jalur read-only
        tidak pernah membuat ApprovalRequest/pending record.

        `ward_tenant` = identitas tenant yang dipakai untuk mengikat WardManager
        (WardGovernanceBoundary ownership). Default = approver (jalur human
        approval). Jalur policy-authorized memakai identitas user peminta yang
        nyata (bukan marker policy), sehingga entrustment Ward tetap tersolve
        (cross-tenant untuk tenant lain tetap fail-closed).
        """
        state = self._state
        _ward_tenant = ward_tenant if ward_tenant is not None else approver
        _metrics.inc("sam_execution_started")
        state.approval_status = approval_status
        state.approval_decision = approval_decision
        state.status = UxStateStatus.RUNNING

        _exec_id = f"exec-{uuid.uuid4().hex[:12]}"
        obs = dict(state.observability or {})
        obs.update(
            {
                "status": UxStateStatus.RUNNING,
                "execution_id": _exec_id,
                "approver": (approval_decision.get("approver") or approver or "user"),
            }
        )
        state.observability = obs

        operation = (self._request.operation or "").strip()
        repo = self._request.target or self._test_repo
        # approval_reason tetap jujur: mencerminkan jalur otorisasi yang dipakai
        # (human approval vs policy-authorized read-only), bukan palsu.
        if approval_status == UxStateStatus.APPROVED:
            _approval_reason = f"APPROVED by {approver or 'user'}"
        else:
            _approval_reason = f"policy-authorized read-only (no human approval; policy: {approver or 'read_only'})"
        try:
            # Dispatcher eksekusi (B1/B2): pilih jalur canonical sesuai operasi.
            # GitHub -> m8_002_build (blok existing di bawah). web.*/http.* ->
            # connector read-only. Operasi lain -> UnsupportedOperationError
            # (BLOCKED jujur, 0 side effect).
            _ward_mgr = _build_ward_manager_for_tenant(_ward_tenant)
            result = run_mission(
                operation=operation,
                target=self._request.target,
                repo=repo,
                artifact_dir=self._artifact_dir,
                approval_reason=_approval_reason,
                # R1-004: cache findings investigasi terakhir (W1). Hanya
                # environment.diagnose yang membaca field ini; yang lain mengabaikan.
                findings=self._last_investigation_findings,
                # R1-005: cache DiagnosisResult CANONICAL terakhir. Hanya
                # environment.recommend yang membaca field ini; yang lain mengabaikan.
                diagnosis=self._last_diagnosis_result,
                ward_manager=_ward_mgr,
            )
        except UnsupportedOperationError as exc:
            state.status = UxStateStatus.BLOCKED
            state.failure_kind = UxFailureKind.BLOCKED
            state.failure_message = str(exc)
            obsb = dict(state.observability or {})
            obsb.update(
                {
                    "status": UxStateStatus.BLOCKED,
                    "end_time": datetime.now(timezone.utc).isoformat(),
                    "verification_result": "none (unsupported - 0 side effect)",
                    "failure_reason": str(exc),
                }
            )
            state.observability = obsb
            self._audit.append(
                {
                    "stage": "execute",
                    "event": "unsupported_operation",
                    "ok": False,
                    "blocked": True,
                    "detail": str(exc),
                }
            )
            self._persist()
            return state
        except Exception as exc:  # noqa: BLE001 — interface harus tetap hidup
            state.status = UxStateStatus.FAILED
            state.failure_kind = UxFailureKind.FAILED
            state.failure_message = f"mission gagal: {exc}"
            obs2 = dict(state.observability or {})
            obs2.update(
                {
                    "status": UxStateStatus.FAILED,
                    "end_time": datetime.now(timezone.utc).isoformat(),
                    "verification_result": "none (gagal di eksekusi)",
                    "failure_reason": str(exc),
                }
            )
            state.observability = obs2
            self._audit.append(
                {
                    "stage": "execute",
                    "event": "mission_failed",
                    "ok": False,
                    "blocked": False,
                    "detail": str(exc),
                }
            )
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
        # M12-008: telemetri hasil eksekusi.
        if state.status == UxStateStatus.COMPLETED:
            _metrics.inc("sam_execution_completed")
        elif state.status == UxStateStatus.FAILED:
            _metrics.inc("sam_execution_failed")
        state.failure_kind = verdict["failure_kind"] or UxFailureKind.NONE
        state.failure_message = "" if verdict["status"] == "completed" else verdict["message"]
        state.result_summary = result.get("title", "") + (
            " (ok)" if result.get("ok") else " (gagal)"
        )

        # M10-003: observability final setelah eksekusi (tanpa secret).
        gh_verify = next(
            (t for t in (result.get("timeline") or []) if t.get("stage") == "verify"),
            None,
        )
        obs3 = dict(state.observability or {})
        obs3.update(
            {
                "status": state.status,
                "end_time": datetime.now(timezone.utc).isoformat(),
                "verification_result": (
                    (gh_verify or {}).get("detail")
                    or (
                        "ok (evidence eksternal)"
                        if state.status == UxStateStatus.COMPLETED
                        else verdict["message"]
                    )
                ),
                "failure_reason": verdict["message"]
                if state.status in (UxStateStatus.BLOCKED, UxStateStatus.FAILED)
                else "",
            }
        )
        state.observability = obs3

        # Evidence chain runut (M9-004).
        timeline = result.get("timeline", []) or []
        state.timeline = [
            {
                "stage": t.get("stage"),
                "ok": t.get("ok"),
                "blocked": t.get("blocked"),
                "detail": t.get("detail", ""),
            }
            for t in timeline
        ]
        # Untuk "what actually happened" (M9-002) — tampilkan issue_url jika ada
        # (nilai dari `scrubbed` boundary; `masked`/secret TIDAK pernah diambil).
        gh = next(
            (
                t
                for t in timeline
                if t.get("stage") in ("github_api", "execute", "act") and t.get("scrubbed")
            ),
            None,
        )
        scrubbed = (gh or {}).get("scrubbed") or {}
        # R1-002: evidence environment nyata (dari timeline environment.observe).
        env_t = next(
            (t for t in timeline if t.get("stage") == "environment.observe"),
            None,
        )
        env_ev = (env_t or {}).get("evidence") or {}
        # R1-003: evidence INVESTIGASI environment (dari timeline environment.investigate).
        env_inv_t = next(
            (t for t in timeline if t.get("stage") == "environment.investigate"),
            None,
        )
        env_inv_ev = (env_inv_t or {}).get("evidence") or {}
        # R1-004: evidence DIAGNOSIS environment (dari timeline environment.diagnose).
        env_diag_t = next(
            (t for t in timeline if t.get("stage") == "environment.diagnose"),
            None,
        )
        env_diag_ev = (env_diag_t or {}).get("evidence") or {}
        # R1-005: evidence RECOMMENDATION environment (dari timeline environment.recommend).
        env_rec_t = next(
            (t for t in timeline if t.get("stage") == "environment.recommend"),
            None,
        )
        env_rec_ev = (env_rec_t or {}).get("evidence") or {}
        if env_rec_t is not None:
            rec_scrubbed = (env_rec_t or {}).get("scrubbed") or {}
            state.evidence = [
                {
                    "kind": "environment_recommendation",
                    "recommendation_count": env_rec_ev.get("recommendation_count", 0),
                    "recommendations": env_rec_ev.get("recommendations", []),
                    "diagnosis_ref": env_rec_ev.get("diagnosis_ref", ""),
                    "summary": env_rec_ev.get("summary", ""),
                    "ok": bool(rec_scrubbed.get("ok")),
                }
            ]
        # R1-004: evidence DIAGNOSIS environment (dari timeline environment.diagnose).
        elif env_diag_t is not None:
            diag_scrubbed = (env_diag_t or {}).get("scrubbed") or {}
            state.evidence = [
                {
                    "kind": "environment_diagnosis",
                    "verdict": env_diag_ev.get("verdict", ""),
                    "confidence": env_diag_ev.get("confidence"),
                    "diagnosis": env_diag_ev.get("diagnosis", []),
                    "evidence_ref": env_diag_ev.get("evidence_ref", ""),
                    "summary": env_diag_ev.get("summary", ""),
                    "sufficiency": env_diag_ev.get("sufficiency", env_diag_ev.get("verdict", "")),
                    "ok": bool(diag_scrubbed.get("ok")),
                }
            ]
            # R1-005: cache DiagnosisResult CANONICAL (objek utuh, bukan Dict)
            # agar misi recommendation berikutnya makan dari diagnosis terakhir.
            if result.get("_canonical_diagnosis") is not None:
                self._last_diagnosis_result = result.get("_canonical_diagnosis")
        elif env_inv_t is not None:
            inv_scrubbed = (env_inv_t or {}).get("scrubbed") or {}
            state.evidence = [
                {
                    "kind": "environment_investigation",
                    "finding_count": env_inv_ev.get("finding_count", 0),
                    "findings": env_inv_ev.get("findings", []),
                    "insufficient": bool(env_inv_ev.get("insufficient")),
                    "summary": env_inv_ev.get("summary", ""),
                    "evidence_ref": env_inv_ev.get("evidence_ref", ""),
                    "ok": bool(inv_scrubbed.get("ok")),
                }
            ]
            # R1-004 W1: cache findings investigasi untuk misi diagnosis terpisah.
            inv_sc = (env_inv_t or {}).get("scrubbed") or {}
            cached = env_inv_ev.get("findings", [])
            if cached:
                self._last_investigation_findings = list(cached)
            elif inv_sc.get("ok") is True or env_inv_ev.get("insufficient"):
                # Investigasi selesai tanpa findings nyata -> simpan kosong agar
                # diagnosis berikutnya jujur INSUFFICIENT (bukan None/unknown).
                self._last_investigation_findings = []
        elif env_t is not None:
            env_scrubbed = (env_t or {}).get("scrubbed") or {}
            state.evidence = [
                {
                    "kind": "environment_observation",
                    "entity_count": env_ev.get("entity_count", 0),
                    "sources": env_ev.get("sources", []),
                    "failures": env_ev.get("failures", []),
                    "entities": env_ev.get("entities", []),
                    "detail": (env_t or {}).get("detail", ""),
                    "ok": bool(env_scrubbed.get("ok")),
                }
            ]
        elif scrubbed.get("ok"):
            state.evidence = [
                {
                    "kind": "external_github_issue",
                    "url": scrubbed.get("issue_url", ""),
                    "number": scrubbed.get("number"),
                    "detail": scrubbed.get("detail", ""),
                }
            ]
        elif result.get("target") and not scrubbed:
            # Non-GitHub (web.*/http.*): rekam target hasil eksekusi sbg evidence
            # read-only (tanpa secret).
            state.evidence = [
                {
                    "kind": "read_only_result",
                    "target": result.get("target", ""),
                    "detail": result.get("detail", ""),
                }
            ]
        state.artifact_ref = result.get("artifact_path", "")
        state.audit_ref = f"audit_count={result.get('audit_count', 0)}"
        # M9-004: append mission timeline ke audit trail (sanitized, no secret).
        for t in result.get("timeline") or []:
            self._audit.append(
                {
                    "stage": t.get("stage"),
                    "ok": t.get("ok"),
                    "blocked": t.get("blocked"),
                    "detail": t.get("detail", ""),
                }
            )
        self._persist()
        return state

    def execute_policy_authorized(self, approver: str = "policy:read_only", ward_tenant: Optional[str] = None) -> UxMissionState:
        """Jalankan read-only Mission TANPA fake approval (W2 Option C).

        Boundary canonical decision: read-only Mission yang `approval_required=False`
        (operation environment.observe/investigate/diagnose/recommend) TIDAK butuh
        human approval — otorisasi datang dari POLICY (capability read-only),
        bukan dari keputusan user. JADI:
          - TIDAK membuat ApprovalRequest/pending record (bukan fake approval).
          - TIDAK memanggil ApprovalCoordinator.decide (tidak ada user intent).
          - TIDAK mengubah approval_required menjadi True (tetap False).
          - Tetap lewat SATU canonical execution boundary = _execute_mission()
            -> run_mission -> WardGovernanceBoundary (identik dgn mission mutating).

        Guard (fail-closed):
          - Mission harus ada & sudah dipahami (UNDERSTOOD).
          - approval_required HARUS False (kalau True -> butuh decide() human).
          - operation HARUS read-only (kalau mutation -> tolak, wajib human approve).

        `approver` = marker otorisasi POLICY (dicatat jujur di approval_decision,
        bukan fake user). `ward_tenant` = identitas tenant NYATA peminta (dipakai
        utk mengikat WardManager agar entrustment Ward tersolve; cross-tenant
        untuk tenant lain tetap fail-closed).
        """
        if self._state is None or self._request is None or self._plan is None:
            raise RuntimeError(
                "tidak ada mission untuk dieksekusi (policy-authorized)"
            )
        state = self._state
        # Fail-closed: hanya Mission yang memang tidak butuh approval boleh lewat
        # jalur policy-authorized. Kalau butuh approval, wajib decide() human.
        if state.approval_required:
            state.status = UxStateStatus.REJECTED
            state.failure_kind = UxFailureKind.REJECTED
            state.failure_message = (
                "Mission butuh human approval \u2014 gunakan decide() \u2014 bukan policy-authorized."
            )
            self._audit.append(
                {
                    "stage": "approval",
                    "event": "denied_policy_authorized_for_approval_required",
                    "ok": False,
                    "blocked": True,
                    "detail": "Mission approval_required=True coba dieksekusi via policy-authorized \u2014 ditolak",
                }
            )
            self._persist()
            return state
        operation = (self._request.operation or "").strip()
        # Guard mutasi: policy-authorized HANYA untuk read-only. Mutation wajib
        # melewati decide() human approval (bukan jalur ini).
        if not self._operation_is_read_only(operation):
            state.status = UxStateStatus.REJECTED
            state.failure_kind = UxFailureKind.REJECTED
            state.failure_message = (
                "Operasi mutating tidak boleh dieksekusi via policy-authorized \u2014 wajib human approval."
            )
            self._audit.append(
                {
                    "stage": "approval",
                    "event": "denied_policy_authorized_for_mutation",
                    "ok": False,
                    "blocked": True,
                    "detail": (
                        f"Operasi {operation} bersifat mutating \u2014 policy-authorized ditolak "
                        "(0 mutation). Wajib decide(approve)."
                    ),
                }
            )
            self._persist()
            return state

        # Otorisasi jujur dari policy (bukan fake approval): ApprovalDecision
        # dicatat dengan approver=policy & reason read-only. TIDAK ada record
        # pending ApprovalRequest yang dibuat di ApprovalCoordinator.
        _policy_decision = {
            "approval_id": f"ap-policy-{uuid.uuid4().hex[:8]}",
            "execution_id": f"policy-{uuid.uuid4().hex[:24]}",
            "approved": True,
            "reason": "read-only operation: no human approval required (policy-authorized)",
            "approver": approver,
        }
        _metrics.inc("sam_mission_policy_authorized")
        self._state = self._execute_mission(
            approval_status="policy_authorized",
            approval_decision=_policy_decision,
            approver=approver,
            ward_tenant=ward_tenant,
        )
        return self._state

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
    def _is_conversational(low: str) -> bool:
        """Deteksi CHAT murni secara deterministik (boundary 2026-08-16).

        Input percakapan biasa (sapaan, terima kasih, identitas diri, kabar,
        acknowledgment) BUKAN mission — operation harus kosong. Guard dijalankan
        SEBELUM LLM agar CHAT vs MISSION deterministik (bukan flaky).
        "kamu bisa apa / apa itu sam" dll -> identitas diri -> CHAT.
        """
        low = (low or "").strip().lower()
        if not low:
            return True
        # Sapaan / greeting
        if re.search(
            r"^(halo|hai|hello|hi|hallo|hei|yo|salam|p\b|selamat\s+(pagi|siang|sore|malam)|assalamualaikum|wr\.?wb)\b",
            low,
        ):
            return True
        # Ucapan terima kasih / sopan santun
        if re.search(r"terima\s*kasih|makasih|thanks|thank\s*you|sama-?sama|maaf(kan)?\b", low):
            return True
        # Identitas diri SAM / pertanyaan umum tentang SAM
        if re.search(
            r"kamu\s+(siapa|itu\s*apa)|siapa\s+kamu|apa\s+itu\s+sam|sam\s+itu\s+apa|"
            r"kamu\s+bisa(\s+apa|\s+melakukan\s+apa)|bisa\s+apa\s*\?|\bkamu\s+apa\b",
            low,
        ):
            return True
        # Kabar / small talk
        if re.search(r"apa\s+kabar|gimana\s+kabar|lagi\s+apa|kabar\s+baik|sedang\s+apa", low):
            return True
        # Acknowledgment singkat
        if re.match(
            r"^(ok|oke|okay|siap|noted|baiklah|baik\b|ya\b|yap|hehe|haha|nggak\b|tidak\b|gitu|ooh|oh\b|hm|hmm|iya|iyaa)\b",
            low,
        ):
            return True
        # Kapabilitas SAM (sync dgn blok identitas di atas, tapi golongan frasa
        # "apa yang bisa kamu lakukan" yang kata-katanya terbalik dari "kamu bisa apa")
        if re.search(
            r"apa\s+(saja|yang|yg)?\s*(bisa|dapat)\s+kamu|yang\s+(bisa|dapat)\s+kamu\s+(lakukan|kerja|buat)|kamu\s+(bisa|dapat)\s+(lakukan|kerja|buat)\s+apa|ada\s+yang\s+(bisa|dapat)\s+kamu\s+(bantu|tolong)",
            low,
        ):
            return True
        # Contextual/explanatory question -> CHAT (prinsip Van: wh-question != CHAT).
        # Guard ini HANYA men-capture wh-question yang TIDAK memuat target sistem
        # environment TANPA kondisi observable: "kenapa?", "kenapa tadi gagal?",
        # "kenapa begitu?" -> CHAT. Bila frasa memuat target sistem +/ kondisi
        # (mis. "kenapa komputer lambat", "kenapa CPU tinggi"), guard TIDAK
        # menyentuhnya -> lolos ke operation resolver (authority) yg menghasilkan
        # environment.investigate. Tidak ada template kalimat literal; murni memakai
        # kosakata domain _ENV_SYSTEM_TARGETS/_ENV_OBSERVABLE_CONDITIONS.
        if (
            re.match(
                r"^(apa|apakah|kenapa|mengapa|bagaimana|kapan|siapa|dimana|di mana|berapa|bisa)",
                low,
            )
            and not _CMD_VERBS.search(low)
            and not _ENV_SYSTEM_TARGETS.search(low)
        ):
            return True
        return False

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

        # 0* ) Guard CHAT deterministik (BOUNDARY 2026-08-16): input percakapan
        #      murni (sapaan / terima kasih / identitas diri / kabar / acknowledgment)
        #      -> operation kosong -> CHAT. Running SEBELUM LLM agar klasifikasi
        #      CHAT vs MISSION deterministik (tidak bergantung flaky LLM yang
        #      kadang mengarang operasi utk percakapan biasa).
        if MissionUXService._is_conversational(low):
            return (
                "",
                "",
                "SAM memahami: ini percakapan biasa, bukan perintah untuk "
                "menjalankan mission. Tidak ada operasi yang dieksekusi.",
                [],
                "",
                "",
                None,
            )

        # 0) Determistik (SEBELUM AI): "periksa komputer saya"-sekelas.
        #    Ini perintah eksplisit yg TIDAK boleh bergantung pada routing AI
        #    lokal yang flaky/MAP (pelajaran S2-4: jangan percaya target dari
        #    AI utk operasi jitu). Bila cocok -> langsung environment.observe.
        env_match = MissionUXService._interpret_environment_observe(low)
        if env_match:
            return env_match + (None,)

        # 0b) Determistik (SEBELUM AI): "diagnosa/simpulkan/apa penyebabnya"-
        #    kelas. R1-004 DIAGNOSIS. Dicek SEBELUM investigate: kata "diagnosa/
        #    simpulkan/kesimpulan" = permintaan EPSILIT kesimpulan/verdict atas
        #    evidence yang SUDAH diproduksi investigasi (di-cache service, W1),
        #    BUKAN "cari bukti baru". Tidak mengarang sebab tanpa evidence.
        diag_match = MissionUXService._interpret_environment_diagnose(low)
        if diag_match:
            return diag_match + (None,)

        # 0b2) Determistik (SEBELUM AI): "rekomendasi/sarankan tindakan"-kelas.
        #    R1-005 RECOMMENDATION. Dicek SETELAH diagnose (diagnosis harus
        #    menghasilkan verdict dulu sebelum rekomendasi). Menilai DiagnosisResult
        #    R1-004 yang di-cache service (canonical) dan menyusun rekomendasi
        #    canonical HANYA bila ada canonical action mapping TERBUKTI; selain itu
        #    recommendations=[] jujur (fail-closed). BUKAN recovery/execution.
        rec_match = MissionUXService._interpret_environment_recommend(low)
        if rec_match:
            return rec_match + (None,)

        # 0c) Determistik (SEBELUM AI): "kenapa/mengapa ... lambat?"-sekelas.
        #    R1-003 INVESTIGATION. Bedakan dari observe: observe = "periksa/
        #    cek/lihat sehat", investigate = "kenapa/mengapa/masalah/selidik".
        #    Investigasi memahami permintaan MENCARI sebab/masalah (menghasilkan
        #    bukti). Berhenti di finding kandidat + confidence; TIDAK menyimpulkan
        #    root cause (itu R1-004); INSUFFICIENT bila evidence tak cukup.
        inv_match = MissionUXService._interpret_environment_investigate(low)
        if inv_match:
            return inv_match + (None,)

        # 1) Coba pemahaman cerdas via AI lokal (Gemma3:1b via Ollama).
        #    Menutup kesenjangan "SAM hanya kenal pola kata" -> SAM bisa
        #    memahami permintaan bahasa bebas. Fallback aman bila offline.
        #    ADR-007: bila LLM mengusulkan operation yang TIDAK admissible
        #    (resolve_reason != None), hasil invalid DI-PERTAHANKAN (bukan
        #    di-fallback ke regex) agar no Mission + alasan ter-track.
        attempt = MissionUXService._interpret_via_ai(t)
        if attempt is not None:
            if attempt[0] or attempt[6]:
                return attempt

        # Fallback: pola regex (mode offline / Ollama tidak tersedia).
        is_github_issue = bool(
            re.search(r"github", low) and re.search(r"(issue|masalah|tiket|new issue|create)", low)
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
            understood = f"SAM memahami: membuat GitHub issue di repo '{target}'."
            planned = [
                "memverifikasi koneksi GitHub (boundary)",
                f"membuat issue di repo '{target}' dengan judul dari permintaan",
                "melakukan verifikasi independen (GET issue dari GitHub)",
            ]
            action_summary = f"SAM akan membuat GitHub issue di repo '{target}'."
            approval_reason = (
                "Tindakan ini menghasilkan efek eksternal nyata pada GitHub "
                "(repo uji). Persetujuan Anda diperlukan sebelum eksekusi."
            )
            return (operation, target, understood, planned, action_summary, approval_reason, None)

        # Fallback web (read-only): "buka website X" / "buka <url>".
        # Tangkap URL eksplisit atau domain, agar target eksekusi benar.
        url_match = re.search(
            r"(https?://[^\s]+|www\.[^\s]+|[a-z0-9-]+\.[a-z]{2,}(?:/[^\s]*)?)",
            t,
            flags=re.I,
        )
        is_web = bool(re.search(r"(buka|brows|open|web|website|site|halaman)", low))
        if is_web:
            operation = "web.open"
            raw_url = (url_match.group(1) if url_match else "") or ""
            target = (
                raw_url if raw_url.startswith("http") else f"https://{raw_url}" if raw_url else ""
            )
            if not target:
                # Tidak ada URL/domain yang ditangkap -> tidak bisa dieksekusi.
                return (
                    "",
                    "",
                    "SAM tidak menemukan URL untuk dibuka pada permintaan ini.",
                    [],
                    "",
                    "",
                    "unresolved",
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
            return (operation, target, understood, planned, action_summary, approval_reason, None)

        # Tidak ada pola regex yang cocok -> unresolved (BUKAN chat: guard
        # CHAT sudah berjalan di awal; ini input yang tidak bisa dipetakan).
        return (
            "",
            "",
            "SAM tidak mengenali operasi pada permintaan ini.",
            [],
            "",
            "",
            "unresolved",
        )

    @staticmethod
    def _operation_is_read_only(operation: str) -> bool:
        """Apakah operasi bersifat read-only (tidak mengubah state eksternal)?

        Menjadi dasar pemisahan `approval_required` dari ke-mission-an (boundary
        audit 2026-08-16): read-only operation (observe/investigate/diagnose/
        recommend) dapat merupakan MISSION tanpa membutuhkan approval, karena
        tidak menghasilkan efek eksternal. Mutation (mis. github.create_issue)
        tetap membutuhkan approval sebagai execution gate NYATA (M9-003/M10-006).
        """
        op = (operation or "").strip().lower()
        # Mutasi nyata (efek eksternal) — butuh approval.
        if op.startswith("github."):
            return False
        # Read-only: hanya environment.* (observe/investigate/diagnose/recommend)
        # yang dijadikan Mission-tanpa-approval (VAN 2026-08-16). web.*/http.*/
        # db.* tetap approval-gated karena menyasar target EKSTERNAL dan dijamin
        # oleh keputusan berdasar test nyata E2E (test_web_open_full_journey).
        if op.startswith("environment."):
            return True
        # Operasi dikenal sbg mission tapi belum tentu read-only -> butuh approval.
        return False

    @staticmethod
    def _interpret_environment_observe(low: str):
        """Deteksi deterministik instruksi observasi environment (R1-002).

        Dicocokkan SEBELUM AI agar perintah eksplisit seperti "periksa komputer
        saya" tidak bergantung pada routing Gemma yang flaky. Mengembalikan
        tuple _interpret bila cocok, atau None.

        Read-only: menemukan entitas nyata (process/port/file/env) TANPA
        katalog aplikasi. Bukan katalog Word/PDF/OpenClaw.
        """
        # Prioritas resolver (satu sumber, prinsip semantic intent): bila frasa
        # mengandung TANYA-SEBAB (kenapa/mengapa/penyebab/masalah/selidik) yg
        # menarget sistem, observe MENYERAH ke investigate (blok 0c). Pemeran:
        # "periksa kenapa komputer lambat" -> environment.investigate (bukan observe).
        # Ini BUKAN template literal; itu keputusan prioritas antar-resolver
        # berdasar ada-tidaknya intent tanya-sebab.
        if re.search(r"(kenapa|mengapa|penyebab|masalah|selidik|investigasi|trouble)\b", low):
            return None

        is_env_observe = bool(
            re.search(
                r"(periksa|cek|scan|inspect|monitor|amati|obs\.?erv|lihat)\s*.{0,40}"
                r"(komputer|pc|mesin|sistem|environment|lokal|host)",
                low,
            )
        ) or bool(
            re.search(
                r"(komputer|pc|mesin|sistem|environment|host)\s*.{0,40}"
                r"(periksa|cek|scan|inspect|monitor|amati|sehat|kesehatan|status)",
                low,
            )
        )
        is_env_show = bool(re.search(r"(ada apa|tunjukkan|daftar|list|apa saja)", low)) and bool(
            re.search(r"(komputer|pc|mesin|sistem|environment|lokal|host)", low)
        )
        if not (is_env_observe or is_env_show):
            return None
        return (
            "environment.observe",
            "local-machine",
            "SAM memahami: mengobservasi environment komputer ini (process, "
            "port, file, variabel lingkungan) secara read-only, tanpa katalog "
            "aplikasi spesifik.",
            [
                "enumerasi process nyata dari environment",
                "enumerasi port listening nyata",
                "enumerasi file dan variabel lingkungan",
                "bangun entity graph + confidence per sumber",
                "laporkan evidence (provenance-aware; probe gagal tetap tercatat)",
            ],
            "SAM akan mengobservasi dan melaporkan environment komputer ini "
            "(read-only, tanpa mengubah apapun).",
            "Operasi ini read-only (mengobservasi environment lokal) - tidak "
            "mengubah state eksternal, namun tetap disediakan persetujuan Anda "
            "untuk transparansi.",
        )

    @staticmethod
    def _interpret_environment_investigate(low: str):
        """Deteksi deterministik instruksi INVESTIGASI environment (R1-003).

        Dicocokkan SEBELUM AI (setelah observe) agar "kenapa komputer lambat?"
        tidak bergantung routing Gemma yang flaky. Mengembalikan tuple _interpret
        bila cocok, atau None.

        Berhenti di Finding kandidat + evidence + confidence; TIDAK menyimpulkan
        penyebab (R1-004). INSUFFICIENT ditangani jujur di bawah (evidence tak
        cukup -> tanpa temuan, tanpa fabrikasi).
        """
        # Investigasi: kata kunci tanya-sebab + target sistem environment/keadaan.
        # Pakai kosakata domain _ENV_SYSTEM_TARGETS/_ENV_OBSERVABLE_CONDITIONS
        # (SATU SUMBER, bukan template literal). "kenapa komputer saya lambat",
        # "kenapa CPU saya tinggi", "periksa kenapa komputer lambat" -> investigate.
        is_env_investigate = bool(
            re.search(
                r"(kenapa|mengapa|apa\s*(yg|yang)|diagnos|selidik|investiga|masalah|"
                r"trouble|sumber|penyebab|kenapa)\b",
                low,
            )
        ) and bool(_ENV_SYSTEM_TARGETS.search(low) or _ENV_OBSERVABLE_CONDITIONS.search(low))
        if not is_env_investigate:
            return None
        return (
            "environment.investigate",
            "local-machine",
            "SAM memahami: menginvestigasi environment komputer ini untuk mencari "
            "temuan kandidat berdasar evidence (read-only). SAM TIDAK menyimpulkan "
            "penyebab final; berhenti di finding kandidat + confidence, atau "
            "INSUFFICIENT bila evidence tidak cukup.",
            [
                "observer/scan environment (process, port, file, env)",
                "bangun entity graph + pilih kandidat dari fakta health",
                "jalankan DiagnosisEngine.investigate() per kandidat",
                "susun findings kandidat + evidence + confidence",
                "laporkan INSUFFICIENT bila evidence tidak cukup (0 fabrikasi)",
            ],
            "SAM akan menginvestigasi environment ini dan melaporkan temuan "
            "kandidat (read-only, tanpa menyimpulkan penyebab).",
            "Operasi ini read-only (menginvestigasi environment lokal) - tidak "
            "mengubah state eksternal, namun tetap disediakan persetujuan Anda "
            "untuk transparansi.",
        )

    @staticmethod
    def _interpret_environment_diagnose(low: str):
        """Deteksi deterministik instruksi DIAGNOSIS environment (R1-004).

        Dicocokkan SEBELUM AI (setelah investigate) agar "diagnosa/simpulkan"
        tidak bergantung routing Gemma yang flaky. Mengembalikan tuple _interpret
        bila cocok, atau None.

        Menilai verdict (causal/candidate/insufficient) atas evidence investigasi
        R1-003 yang di-cache service (W1). Tanpa investigasi -> cache kosong ->
        INSUFFICIENT jujur. TIDAK mengarang penyebab.
        """
        is_env_diagnose = bool(
            re.search(
                r"(diagnos|diagnosa|diagnosis|simpulkan|kesimpulan|"
                r"apa\s*penyebab|root\s*cause|sebab(?:nya\s*apa|nya)?)",
                low,
            )
        )
        if not is_env_diagnose:
            return None
        return (
            "environment.diagnose",
            "local-machine",
            "SAM memahami: menilai verdict diagnosis atas evidence investigasi "
            "environment sebelumnya (read-only). Tidak mengarang penyebab bila "
            "evidence belum cukup.",
            [
                "ambil selected evidence dari investigasi terakhir",
                "klasifikasi sinyal kausal yang dibawa evidence",
                "hitung evidence confidence (reuse assessor)",
                "susun verdict causal/candidate/insufficient + diagnosis",
                "INSUFFICIENT jujur bila belum ada investigasi / tanpa sinyal kausal",
            ],
            "SAM akan menilai verdict diagnosis atas temuan investigasi environment "
            "(read-only, tanpa menyimpulkan sebab tanpa evidence).",
            "Operasi ini read-only (menilai diagnosis berbasis evidence) - tidak "
            "mengubah state eksternal, namun tetap disediakan persetujuan Anda untuk "
            "transparansi.",
        )

    @staticmethod
    def _interpret_environment_recommend(low: str):
        """Deteksi deterministik instruksi RECOMMENDATION environment (R1-005).

        Dicocokkan SETELAH diagnose (recommend memerlukan diagnosis yang sudah
        menghasilkan verdict). Mengembalikan tuple _interpret bila cocok, atau None.

        Menilai DiagnosisResult canonical R1-004 (di-cache service) dan menyusun
        rekomendasi canonical HANYA bila ada canonical action mapping TERBUKTI;
        bila tidak -> recommendations=[] jujur (fail-closed). Bukan recovery/execution.
        """
        is_env_recommend = bool(
            re.search(
                r"(rekomend|recommend|sarank?an|tindakan\s+yang\s+layak|"
                r"tindakan\s+apa|remediasi|perbaikan\s+yang\s+disarankan)",
                low,
            )
        )
        if not is_env_recommend:
            return None
        return (
            "environment.recommend",
            "local-machine",
            "SAM memahami: menyusun rekomendasi tindakan atas diagnosis environment "
            "sebelumnya (read-only). Rekomendasi mutation HANYA dibuat bila ada "
            "canonical action mapping terbukti; selain itu rekomendasi kosong jujur.",
            [
                "ambil DiagnosisResult canonical dari diagnosis terakhir",
                "klasifikasi verdict (insufficient/candidate/causal)",
                "hanya causal + canonical action mapping TERBUKTI -> rekomendasi",
                "insufficient/candidate/tanpa mapping -> rekomendasi kosong jujur",
                "STOP sebelum approval/execution (R1-006 terpisah)",
            ],
            "SAM akan menyusun rekomendasi tindakan atas diagnosis environment "
            "(read-only, berhenti sebelum eksekusi).",
            "Operasi ini read-only (menyusun rekomendasi) - tidak mengubah state "
            "eksternal, namun tetap disediakan persetujuan Anda untuk transparansi.",
        )

    # ------------------------------------------------------------------
    # pemahaman cerdas via AI lokal (Gemma3:1b / Ollama) — tanpa internet
    # ADR-007 (APPROVED FOR IMPLEMENTATION 2026-08-17): exact canonical
    # operation set = capability yang memiliki jalur execution canonical nyata
    # (runner.run_mission). INTERNAL use: `_resolve_capability` validasi admission
    # di lapisan interpret; `_AI_CAPABILITIES` (paparan ke LLM) DISINKRONKAN dari
    # sini (C3 single authority) — capability tanpa jalur eksekusi TIDAK diiklankan.
    # NOTE: runner internal tetap prefix-tolerant (github.*/http.<any>), tapi
    # admission rule intent boundary = EXACT set ini (keputusan Van Q1). Runner
    # TIDAK diubah dalam scope ADR-007 (technical debt dicatat terpisah).
    _AI_EXECUTION_CAPABILITIES = frozenset(
        {
            "github.create_issue",  # mutating (M8-006/M9 PROVEN)
            "web.open",  # read-only browser (Q2 Van: web.get TIDAK diadvertise)
            "http.call",  # read-only HTTP
            "environment.observe",  # read-only R1-002
            "environment.investigate",  # read-only R1-003
            "environment.diagnose",  # read-only R1-004
            "environment.recommend",  # read-only R1-005
        }
    )

    _AI_CAPABILITIES = (
        "Operasi SAM yang diketahui: "
        "[github.create_issue] buat/tingkat issue GitHub; "
        "[web.open] buka/baca halaman web; "
        "[http.call] panggil API/HTTP eksternal; "
        "[environment.observe] periksa/observasi komputer/environment lokal (read-only); "
        "[environment.investigate] investigasi/mencari sebab/masalah di komputer/environment "
        "lokal (read-only, berhenti di finding kandidat); "
        "[environment.diagnose] simpulkan/verdict atas evidence investigasi (read-only); "
        "[environment.recommend] rekomendasi tindakan atas diagnosis (read-only). "
        "Jika permintaan hanya percakapan biasa / sapaan / pertanyaan umum (bukan "
        "perintah eksekusi), gunakan operation KOSONG tanpa nama operasi."
    )

    @staticmethod
    def _resolve_capability(operation: str) -> Optional[Tuple[str, str]]:
        """ADR-007: exact canonical admission validator (deterministic authority).

        LLM = CANDIDATE, bukan authority. SAM memutuskan apakah operation
        candidate admissible (termasuk exact canonical execution set).

        Returns:
            (resolved_operation, None)  bila valid & exact canonical.
            (None, resolve_reason)      bila invalid (bukan Mission).
        """
        op = (operation or "").strip().lower()
        if op in MissionUXService._AI_EXECUTION_CAPABILITIES:
            return (op, None)
        return (None, "unsupported_operation")

    @staticmethod
    def _interpret_via_ai(text: str) -> Optional[Tuple[str, str, str, List[str], str, str, Optional[str]]]:
        """Pahami permintaan via LLM reasoning (DeepSeek dulu, fallback Ollama).

        Prioritas provider (REAL reasoning, bukan hanya regex):
          1. DeepSeek (cloud, DEEPSEEK_API_KEY dari env Windows) — sistem PICAKAN.
          2. Ollama lokal (gemma3:1b) — fallback offline/tanpa internet.
          3. regex (mode offline penuh) — dipanggil caller bila None.

        Menghasilkan JSON terstruktur. Bila SEMUA LLM tidak tersedia / timeout /
        hasil tidak valid -> kembalikan None (caller fallback ke regex).
        Aman: tidak ada side effect bila gagal; tidak pernah menetapkan repo.
        """
        if not text.strip():
            return None
        prompt = (
            f"{MissionUXService._AI_CAPABILITIES}\n\n"
            "Instruksi: Dari permintaan berikut, tentukan operasi SAM yang paling "
            "cocok (di antara daftar di atas). Jika tidak cocok sama sekali, pakai "
            "operation kosong. Jawab HANYA dengan JSON valid tanpa teks lain, format:\n"
            '{"operation": "<salah satu operation atau "">", '
            '"target": "<objek sasaran, atau kosong>", '
            '"understood": "<kalimat singkat apa yang SAM pahami>", '
            '"planned": ["<langkah 1>", "<langkah 2>"]}\n\n'
            f"Permintaan: {text}"
        )
        # 1) DeepSeek (provider REAL, cloud) — prioritas utama.
        try:
            from sam.providers.execution.provider_executor import (
                ProviderExecutor,
                ProviderUnavailableError,
            )

            executor = ProviderExecutor()
            raw = executor.execute(
                "deepseek",
                "chat",
                {"prompt": prompt, "model": "deepseek-chat", "max_tokens": 256, "temperature": 0.1},
                timeout_seconds=45,
            )
            parsed = MissionUXService._parse_ai_json(MissionUXService._extract_ai_text(raw))
            if parsed:
                out = MissionUXService._assemble_interpretation(parsed, source="DeepSeek")
                if out is not None:
                    return out
        except (ProviderUnavailableError, Exception):  # noqa: BLE001
            pass  # fallback ke Ollama

        # 2) Ollama lokal (gemma3:1b) — fallback offline, zero internet.
        try:
            from sam.providers.execution.provider_executor import (
                ProviderExecutor,
                ProviderUnavailableError,
            )

            executor = ProviderExecutor()
            raw = executor.execute(
                "ollama",
                "chat",
                {"prompt": prompt, "model": "gemma3:1b", "max_tokens": 256},
                timeout_seconds=90,
            )
            parsed = MissionUXService._parse_ai_json(MissionUXService._extract_ai_text(raw))
            if parsed:
                out = MissionUXService._assemble_interpretation(parsed, source="Ollama")
                if out is not None:
                    return out
        except (ProviderUnavailableError, Exception):  # noqa: BLE001
            pass  # fallback regex di caller
        return None

    @staticmethod
    @staticmethod
    def _assemble_interpretation(
        parsed: Dict[str, Any], source: str
    ) -> Optional[Tuple[str, str, str, List[str], str, str, Optional[str]]]:
        """Susun tuple interpretasi dari JSON LLM (shared DeepSeek/Ollama).

        Source dimasukkan ke understood/reason agar UI jujur dari mana SAM
        menalar. ADR-007: candidate operation dari LLM DIPERIKSA terhadap exact
        canonical capability set (deterministic authority). candidate yang tidak
        admissible -> operation="" (no Mission) + resolve_reason di elemen ke-7.
        Tidak pernah menentukan repo GitHub dari AI (S2-4); repo selalu dikunci
        ke GITHUB_TEST_REPO / default (hanya utk operation github yang VALID).
        """
        operation = str(parsed.get("operation") or "")
        # ai.think bukan operasi Mission nyata (tidak ada jalur eksekusi di
        # runner.py) — ia mewakili CHAT/percakapan biasa. Boundary audit
        # 2026-08-16: CHAT harus operation kosong (bukan Mission). Jadi
        # permintaan yang hanya ingin SAM "berpikir/menjawab" -> bukan misi ->
        # None, dan caller menangani sbg CHAT (operation="").
        if operation in ("ai.think", "ai.chat", "chat"):
            return None
        if not operation:
            return None  # belum operasi yang dikenali -> biarkan fallback/tolak
        # ADR-007: exact canonical admission (DDL authority). LLM hanya candidate.
        resolved, resolve_reason = MissionUXService._resolve_capability(operation)
        if resolved is None:
            # candidate TIDAK admissible: BUKAN Mission, BUKAN CHAT -> invalid/
            # unresolved. operation="" mencegah promosi ke plan/approval/execution;
            # resolve_reason disalurkan ke observability utk audit/debug.
            # target tidak pernah diset (tidak ada jalur eksekusi utk invalid).
            return (
                "",
                "",
                f"SAM tidak dapat memetakan '{operation}' ke capability SAM "
                "yang sudah terbukti (unsupported_operation). Tidak ada operasi "
                "yang akan dijalankan.",
                [],
                "",
                "",
                resolve_reason,
            )
        operation = resolved
        target = str(parsed.get("target") or "")
        if operation == "github.create_issue":
            target = os.environ.get("GITHUB_TEST_REPO") or DEFAULT_TEST_REPO
        elif not target:
            target = ""  # ADR-007: target default repo TIDAK diterapkan ke non-github
        understood = str(parsed.get("understood") or "").strip()
        if understood and not understood.startswith("SAM memahami"):
            understood = f"SAM memahami: {understood}"
        elif not understood:
            understood = f"SAM memahami: menjalankan operasi '{operation}'."
        planned_raw = parsed.get("planned") or []
        planned = [str(x) for x in planned_raw if str(x)] or [
            "melakukan operasi {}".format(operation)
        ]
        action_summary = f"SAM akan menjalankan operasi '{operation}'"
        if target:
            action_summary += f" pada '{target}'"
        reason = (
            f"Pemahaman dihasilkan LLM ({source}). Tindakan ini dapat "
            "menghasilkan efek eksternal; persetujuan Anda diperlukan."
        )
        return (operation, target, understood, planned, action_summary, reason, None)

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
                d = _json.loads(content[start : end + 1])
                if isinstance(d, dict):
                    return d
        except Exception:  # noqa: BLE001
            pass
        return None
