"""
OP-315 — Guardian Conversation

Conversation dapat bertanya:
  - why rejected
  - why approved
  - current guardian state
  - policy violations
  - pending gate
  - recommendation history
  - guardian health
  - guardian statistics

Read only.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class GuardianConversationResponse:
    answer: str
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"answer": self.answer, "data": self.data}


class GuardianConversation:
    """
    Query conversation untuk guardian.
    Read only — tidak mengubah state guardian.
    """

    def __init__(self, coordinator: Any, gate: Any, policy_engine: Any, state: Any,
                 audit: Any, dashboard: Any):
        self._coordinator = coordinator
        self._gate = gate
        self._policy = policy_engine
        self._state = state
        self._audit = audit
        self._dashboard = dashboard

    def why_rejected(self, gate_result: Any = None) -> GuardianConversationResponse:
        """Mengapa proposal ditolak oleh gate."""
        if gate_result is None:
            return GuardianConversationResponse(
                answer="Tidak ada gate result untuk dianalisis."
            )
        rejection = getattr(gate_result, "rejection", None)
        if not rejection:
            return GuardianConversationResponse(
                answer="Proposal tidak ditolak — gate passed."
            )
        return GuardianConversationResponse(
            answer=(
                f"Proposal ditolak oleh gate.\n"
                f"Gate check: {getattr(rejection, 'gate_check', 'unknown')}\n"
                f"Alasan: {getattr(rejection, 'reason', 'N/A')}\n"
                f"Detail: {getattr(rejection, 'detail', 'N/A')}"
            ),
            data=getattr(rejection, "to_dict", lambda: {})() if hasattr(rejection, "to_dict") else None,
        )

    def why_approved(self, gate_result: Any = None) -> GuardianConversationResponse:
        """Mengapa proposal disetujui oleh gate."""
        if gate_result is None:
            return GuardianConversationResponse(
                answer="Tidak ada gate result."
            )
        if not getattr(gate_result, "passed", False):
            return GuardianConversationResponse(answer="Proposal tidak disetujui.")
        checks = []
        if getattr(gate_result, "checked_approval", False):
            checks.append("approval")
        if getattr(gate_result, "checked_evidence", False):
            checks.append("evidence")
        if getattr(gate_result, "checked_confidence", False):
            checks.append("confidence")
        if getattr(gate_result, "checked_policy", False):
            checks.append("policy")
        if getattr(gate_result, "checked_trust", False):
            checks.append("trust")
        if getattr(gate_result, "checked_mission", False):
            checks.append("mission state")
        return GuardianConversationResponse(
            answer=f"Proposal disetujui. Semua gate check lulus: {', '.join(checks)}."
        )

    def current_guardian_state(self) -> GuardianConversationResponse:
        """State guardian saat ini."""
        gs = getattr(self._state, "state", None)
        if gs is None:
            return GuardianConversationResponse(answer="Guardian state tidak tersedia.")
        text = (
            f"Status: {getattr(gs, 'status', 'unknown')}\n"
            f"Pipeline: {'berjalan' if getattr(gs, 'pipeline_running', False) else 'idle'}\n"
            f"Gate: {'aktif' if getattr(gs, 'gate_active', False) else 'nonaktif'}\n"
            f"Policy: {'aktif' if getattr(gs, 'policy_enabled', False) else 'nonaktif'}\n"
            f"Audit: {'aktif' if getattr(gs, 'audit_active', False) else 'nonaktif'}\n"
            f"Pipeline terakhir: {getattr(gs, 'last_pipeline_at', 'N/A')}\n"
            f"Error: {getattr(gs, 'error_count', 0)}"
        )
        return GuardianConversationResponse(answer=text, data=getattr(gs, "to_dict", lambda: {})())

    def policy_violations(self, limit: int = 10) -> GuardianConversationResponse:
        """Daftar policy violations."""
        audit = self._audit
        if audit is None:
            return GuardianConversationResponse(answer="Audit tidak tersedia.")
        try:
            violations = audit.get_violations(limit=limit) if hasattr(audit, "get_violations") else []
        except Exception:
            violations = []
        if not violations:
            return GuardianConversationResponse(answer="Tidak ada policy violations.")
        lines = [f"  {i+1}. {v}" for i, v in enumerate(violations)]
        return GuardianConversationResponse(answer="Policy violations:\n" + "\n".join(lines))

    def pending_gate(self) -> GuardianConversationResponse:
        """Proposal yang sedang menunggu gate."""
        return GuardianConversationResponse(
            answer="Gate evaluation bersifat synchronous — tidak ada antrian pending."
        )

    def recommendation_history(self, limit: int = 5) -> GuardianConversationResponse:
        """Riwayat rekomendasi."""
        audit = self._audit
        if audit is None:
            return GuardianConversationResponse(answer="Audit tidak tersedia.")
        try:
            recs = audit.get_recommendations(limit=limit) if hasattr(audit, "get_recommendations") else []
        except Exception:
            recs = []
        if not recs:
            return GuardianConversationResponse(answer="Tidak ada riwayat rekomendasi.")
        lines = [f"  {i+1}. {r}" for i, r in enumerate(recs)]
        return GuardianConversationResponse(answer="Riwayat rekomendasi:\n" + "\n".join(lines))

    def guardian_health(self) -> GuardianConversationResponse:
        """Kesehatan guardian."""
        health = getattr(self._state, "health", None)
        if health is None:
            return GuardianConversationResponse(answer="Health data tidak tersedia.")
        text = (
            f"Overall: {getattr(health, 'overall', 'unknown')}\n"
            f"Coordinator: {'sehat' if getattr(health, 'coordinator_healthy', False) else 'bermasalah'}\n"
            f"Gate: {'sehat' if getattr(health, 'gate_healthy', False) else 'bermasalah'}\n"
            f"Policy: {'sehat' if getattr(health, 'policy_healthy', False) else 'bermasalah'}\n"
            f"Audit: {'sehat' if getattr(health, 'audit_healthy', False) else 'bermasalah'}\n"
            f"Conversation: {'sehat' if getattr(health, 'conversation_healthy', False) else 'bermasalah'}\n"
            f"Dashboard: {'sehat' if getattr(health, 'dashboard_healthy', False) else 'bermasalah'}\n"
            f"Terakhir cek: {getattr(health, 'last_health_check', 'N/A')}"
        )
        if hasattr(health, "issues") and health.issues:
            text += "\n\nIssues:\n" + "\n".join(f"  - {i}" for i in health.issues)
        return GuardianConversationResponse(answer=text)

    def guardian_statistics(self) -> GuardianConversationResponse:
        """Statistik guardian."""
        stats = getattr(self._state, "statistics", None)
        if stats is None:
            return GuardianConversationResponse(answer="Statistik tidak tersedia.")
        text = (
            f"Total pipelines: {getattr(stats, 'total_pipelines', 0)}\n"
            f"Gate passed: {getattr(stats, 'passed_gate', 0)}\n"
            f"Gate rejected: {getattr(stats, 'rejected_gate', 0)}\n"
            f"Policy violations: {getattr(stats, 'policy_violations', 0)}\n"
            f"Approvals waiting: {getattr(stats, 'approvals_waiting', 0)}\n"
            f"Approvals completed: {getattr(stats, 'approvals_completed', 0)}\n"
            f"Reasonings completed: {getattr(stats, 'reasonings_completed', 0)}\n"
            f"Proposals submitted: {getattr(stats, 'proposals_submitted', 0)}\n"
            f"Rata-rata pipeline: {getattr(stats, 'average_pipeline_ms', 0):.1f} ms\n"
            f"Uptime: {getattr(stats, 'uptime_hours', 0):.1f} hours"
        )
        return GuardianConversationResponse(answer=text)
