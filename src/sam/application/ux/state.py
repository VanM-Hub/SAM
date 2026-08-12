"""UxMissionState — ViewModel state observable untuk UI (M9-004/005/006).

Satu object yang memberi UI "keadaan sebenarnya" dalam bahasa manusia:
  request -> understanding -> plan -> approval -> result -> evidence -> audit
plus failure semantics yang bisa dibedakan:
  - BLOCKED   : credential/kredibilitas hilang (mis. "AI provider tidak dapat
                digunakan karena credential belum tersedia") — BUKAN "AI failed".
  - FAILED    : eksekusi gagal (mis. GitHub token invalid / HTTP 4xx-5xx).
  - REJECTED  : approval ditolak user (berbeda dari FAILED).
  - RETRYABLE : timeout/lainnya yang bisa dicoba ulang.
  - COMPLETED : berhasil + evidence + audit tersedia.

Tidak pernah berisi nilai secret. Mengandung `chain` urut yang bisa ditelusuri
(M9-004) untuk operator.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class UxStateStatus(str):
    NONE = "none"
    RECEIVED = "received"
    UNDERSTOOD = "understood"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    RETRYABLE = "retryable"


class UxFailureKind(str):
    NONE = ""
    BLOCKED = "blocked"
    FAILED = "failed"
    REJECTED = "rejected"
    RETRYABLE = "retryable"


@dataclass
class UxMissionState:
    """State mission yang disajikan ke UI (bahasa manusia)."""

    request_id: str = ""
    # Request
    request_text: str = ""
    # Understanding
    what_sam_understood: str = ""
    operation: str = ""
    target: str = ""
    # Plan
    planned_steps: List[str] = field(default_factory=list)
    approval_required: bool = False
    action_summary: str = ""
    # Approval
    approval_status: str = UxStateStatus.NONE
    approval_decision: Optional[Dict[str, Any]] = None
    # Execution
    status: str = UxStateStatus.NONE
    failure_kind: str = UxFailureKind.NONE
    failure_message: str = ""        # bahasa manusia, bukan stack trace
    result_summary: str = ""
    # Evidence & artifact & audit
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    artifact_ref: str = ""
    audit_ref: str = ""
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    # M10-003 Observability: field yang menjawab "SAM lakukan apa, mengapa,
    # atas persetujuan siapa, ke sistem mana, bagaimana tahu hasil benar".
    # Tanpa secret leakage — ini murni metadata operasional.
    observability: Dict[str, Any] = field(default_factory=dict)
    # metadata
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "request": self.request_text,
            "understanding": {
                "what_sam_understood": self.what_sam_understood,
                "operation": self.operation,
                "target": self.target,
            },
            "plan": {
                "planned_steps": list(self.planned_steps),
                "approval_required": self.approval_required,
                "action_summary": self.action_summary,
            },
            "approval": {
                "status": self.approval_status,
                "decision": self.approval_decision,
            },
            "execution": {
                "status": self.status,
                "failure_kind": self.failure_kind,
                "failure_message": self.failure_message,
                "result_summary": self.result_summary,
            },
            "evidence": list(self.evidence),
            "artifact_ref": self.artifact_ref,
            "audit_ref": self.audit_ref,
            "timeline": list(self.timeline),
            "observability": dict(self.observability),
            "updated_at": self.updated_at,
        }


def ux_state() -> UxMissionState:
    """Factory helper — default state kosong."""
    return UxMissionState()
