"""MissionRequest — request manusia yang masuk via UI (DTO immutable).

Ini SATU-SATUNYA bentuk input yang diterima product entry point (M9-001).
UI tidak boleh mengirim struktur internal (ProviderExecutor, ExecutionContract,
GovernanceDecision); semua di-normalisasi ke sini.

Pola: immutable dataclass; `as_dict()` menyajikan bahasa yang aman untuk UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


class MissionRequestStatus(str):
    DRAFT = "draft"            # baru dibuat di sisi UI/request
    RECEIVED = "received"      # sudah diterima product entry point
    UNDERSTOOD = "understood"  # SAM sudah memahaminya (menyusun rencana)
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class MissionRequest:
    """Request manusia. Immutable — request harus diganti, bukan diubah."""

    request_id: str
    text: str                                   # apa yang manusia minta (bahasa alami)
    operation: str = ""                         # "github.create_issue" dst (dari SAM understanding)
    target: str = ""                            # target aman (mis. repo test yang diizinkan)
    payload: Dict[str, str] = field(default_factory=dict)
    status: str = MissionRequestStatus.RECEIVED
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "text": self.text,
            "operation": self.operation,
            "target": self.target,
            "payload": dict(self.payload),
            "status": self.status,
            "created_at": self.created_at,
        }
