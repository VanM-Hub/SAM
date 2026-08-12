"""MissionPlan — rencana yang SAM susun dari request (ViewModel, M9-002).

Di sinilah "bahasa internal" diterjemahkan ke bahasa manusia sebelum sampai
ke UI. UI TIDAK melihat ProviderExecutor/CapabilityRegistry/ExecutionContract;
UI melihat:
  - what_sam_understood : apa yang SAM pahami dari request
  - planned_steps      : apa yang SAM rencanakan (urutan, bahasa manusia)
  - approval_required  : apakah langkah ini butuh persetujuan manusia
  - confidence / risk  : ringkas, aman untuk pengguna (opsional)

Immutable. Dibangun oleh product entry point, BUKAN oleh UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


class MissionPlanStatus(str):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"


@dataclass(frozen=True)
class MissionPlan:
    """Rencana yang aman ditampilkan ke UI (bahasa manusia, bukan jargon)."""

    plan_id: str
    request_id: str
    what_sam_understood: str          # bahasa manusia
    planned_steps: List[str] = field(default_factory=list)  # bahasa manusia
    approval_required: bool = True
    approval_reason: str = ""         # mengapa perlu approval
    status: str = MissionPlanStatus.PENDING_APPROVAL
    risk_summary: str = ""            # ringkas; "" bila tidak ada
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "request_id": self.request_id,
            "what_sam_understood": self.what_sam_understood,
            "planned_steps": list(self.planned_steps),
            "approval_required": self.approval_required,
            "approval_reason": self.approval_reason,
            "status": self.status,
            "risk_summary": self.risk_summary,
            "created_at": self.created_at,
        }
