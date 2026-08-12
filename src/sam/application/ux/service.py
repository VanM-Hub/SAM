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


# Repo test default untuk GitHub mutation (repo TEST, bukan production).
DEFAULT_TEST_REPO = "VanM-Hub/test-issues"


class MissionUXService:
    """Product entry point untuk UI. In-memory per-request store."""

    def __init__(
        self,
        test_repo: str = DEFAULT_TEST_REPO,
        artifact_dir: str = "docs/engineering/reports",
    ) -> None:
        self._test_repo = test_repo or DEFAULT_TEST_REPO
        self._artifact_dir = artifact_dir
        self._request: Optional[MissionRequest] = None
        self._plan: Optional[MissionPlan] = None
        self._approval = ApprovalCoordinator()
        self._state: Optional[UxMissionState] = None
        self._last_result: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # 1) submit — terima request manusia, SAM pahami, susun rencana, TARUH
    #    di WAITING_APPROVAL. Tidak ada eksekusi di sini.
    # ------------------------------------------------------------------
    def submit(self, text: str) -> UxMissionState:
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

        # Pending approval (UI akan menampilkan [Approve][Reject]).
        action = action_summary or f"SAM akan: {planned[0] if planned else 'melakukan tindakan'}"
        approval_req = ApprovalRequest(
            approval_id=f"apr-{uuid.uuid4().hex[:8]}",
            plan_id=plan.plan_id,
            request_id=req.request_id,
            action_summary=action,
            gates=[s for s in planned],
        )
        self._approval.record_pending(approval_req)

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
        self._state = state
        return state

    # ------------------------------------------------------------------
    # 2) decide — user klik Approve/Reject (M9-003). Real gate.
    # ------------------------------------------------------------------
    def decide(self, intent: ApprovalDecisionIntent, approver: str = "user") -> UxMissionState:
        if self._state is None or self._request is None or self._plan is None:
            raise RuntimeError("tidak ada mission yang sedang menunggu approval")

        outcome = self._approval.decide(intent, approver=approver)
        state = self._state

        if outcome.status == ApprovalStatus.REJECTED:
            # User reject -> REJECTED, eksekusi TIDAK pernah berjalan.
            state.approval_status = UxStateStatus.REJECTED
            state.status = UxStateStatus.REJECTED
            state.failure_kind = UxFailureKind.REJECTED
            state.failure_message = "Mission ditolak oleh pengguna — tidak ada eksekusi."
            state.approval_decision = outcome.as_dict()
            return state

        # outcome == APPROVED -> jalankan mission nyata via jalur canonical.
        state.approval_status = UxStateStatus.APPROVED
        state.approval_decision = outcome.as_dict()
        state.status = UxStateStatus.RUNNING

        repo = self._request.target or self._test_repo
        try:
            result = run_github_real_mission(repo=repo, artifact_dir=self._artifact_dir)
        except Exception as exc:  # noqa: BLE001 — interface harus tetap hidup
            state.status = UxStateStatus.FAILED
            state.failure_kind = UxFailureKind.FAILED
            state.failure_message = f"mission gagal: {exc}"
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
        if not self._last_result:
            return []
        # Sanitize: tidak pernah masukkan secret (timeline step bukan tempat secret).
        return [
            {"stage": t.get("stage"), "ok": t.get("ok"), "blocked": t.get("blocked"),
             "detail": t.get("detail", "")}
            for t in (self._last_result.get("timeline") or [])
        ]

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
