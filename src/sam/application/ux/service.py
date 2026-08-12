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
from sam.application.ux.runner import classify_mission_outcome, run_github_real_mission
from sam.application.ux.state import UxMissionState, UxFailureKind, UxStateStatus
from sam.application.ux.store import MissionStore


# Repo test default untuk GitHub mutation (repo TEST, bukan production).
DEFAULT_TEST_REPO = "VanM-Hub/test-issues"


class MissionUXService:
    """Product entry point untuk UI. In-memory per-request store."""

    def __init__(
        self,
        test_repo: str = DEFAULT_TEST_REPO,
        artifact_dir: str = "docs/engineering/reports",
        store: Optional["MissionStore"] = None,
    ) -> None:
        self._test_repo = test_repo or DEFAULT_TEST_REPO
        self._artifact_dir = artifact_dir
        self._request: Optional[MissionRequest] = None
        self._plan: Optional[MissionPlan] = None
        self._approval = ApprovalCoordinator()
        self._state: Optional[UxMissionState] = None
        self._last_result: Optional[Dict[str, Any]] = None
        self._audit: List[Dict[str, Any]] = []
        # M10-007: persistensi — restart TIDAK menghilangkan operational truth.
        self._store = store or MissionStore()
        self._idem: Dict[str, Dict[str, Any]] = {}  # {key: {request_id, text}}
        self._recover_from_store()

    # ------------------------------------------------------------------
    # M10-007 — persistence/recovery: restart TIDAK menghilangkan truth.
    # ------------------------------------------------------------------
    def _recover_from_store(self) -> None:
        """Restore state mission terakhir dari disk (recovery setelah restart).
        Membangun kembali UxMissionState dari dict yang dipersist. Dipanggil
        dalam __init__; saling toleran bila file belum ada / korup."""
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
        self._audit = [dict(e) for e in (data.get("audit") or [])]
        # Restore idempotency map (request_id + text) utk mencegah retry ganda.
        for k, v in (data.get("idem") or {}).items():
            self._idem[k] = dict(v)

    def _persist(self) -> None:
        """Snapshot state mission + audit + idem ke disk (tanpa secret)."""
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

    # ------------------------------------------------------------------
    # 1) submit — terima request manusia, SAM pahami, susun rencana, TARUH
    #    di WAITING_APPROVAL. Tidak ada eksekusi di sini.
    # ------------------------------------------------------------------
    def submit(self, text: str, idempotency_key: Optional[str] = None) -> UxMissionState:
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

        repo = self._request.target or self._test_repo
        try:
            result = run_github_real_mission(repo=repo, artifact_dir=self._artifact_dir)
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
        """Deteksi operasi dari teks. Bahasa manusia -> rencana manusia.

        Returns: (operation, target, understood, planned_steps, action_summary, reason)
        operation "" -> tidak dikenali, tidak ada eksekusi direncanakan.
        """
        t = (text or "").strip()
        low = t.lower()

        # Pola "github create issue / buat issue / new issue".
        is_github_issue = bool(
            re.search(r"github", low)
            and re.search(r"(issue|masalah|tiket|new issue|create)", low)
        )

        if is_github_issue:
            operation = "github.create_issue"
            # Default repo = test repo (repo uji, bukan production). Env override.
            target = os.environ.get("GITHUB_TEST_REPO") or "VanM-Hub/test-issues"
            # Judul issue = seluruh request, kecuali terlihat ada judul eksplisit.
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
            # Pakai judul di payload agar mission canonical mengetahui judul.
            # Disimpan di MissionRequest.payload oleh submit; tapi kita kembalikan
            # via planned + action. Payload aktual dipasang oleh submit caller
            # dengan payload={"title": ..., "body": ...}.
            return (
                operation, target, understood, planned, action_summary, approval_reason
            )

        # Tidak dikenali -> rencana kosong, tidak ada approval.
        return (
            "",
            "",
            "SAM tidak mengenali operasi pada permintaan ini.",
            [],
            "",
            "",
        )
