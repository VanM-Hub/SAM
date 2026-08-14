"""M14-005 AutomaticEscalation — menaikkan tindakan ke manusia bila perlu.

FLOW M14: "Jika authority tidak cukup: ESCALATE. Jika evidence tidak cukup:
ESCALATE. Jika verification gagal: FAILED / ROLLBACK / ESCALATE."

Modul ini memakai ulang EscalationManager (autonomy/escalation.py) yang sudah
ada — bukan membuat escalation engine baru. Ia hanya menyambungkan keputusan
authority/verification -> escalation request + menyediakan keputusan manusia
(approve/reject) yang tetap lewat jalur canonical.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sam.autonomy.escalation import (
    EscalationManager, EscalationRequest,
    DECISION_APPROVE, DECISION_REJECT,
)
from sam.delegated_authority.authority import AuthorityVerdict, AutonomousAuthority


class EscalationReason(str):
    AUTHORITY = "authority"
    EVIDENCE = "evidence"
    VERIFICATION = "verification"
    POLICY = "policy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EscalationOutcome:
    """Hasil eskalasi (apa yang diputuskan manusia, auditable)."""

    escalation_id: str
    reason: str
    decided: bool                 # False bila masih pending / expired / reject
    approve: bool = False
    reject: bool = False
    note: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "escalation_id": self.escalation_id,
            "reason": self.reason,
            "decided": self.decided,
            "approve": self.approve,
            "reject": self.reject,
            "note": self.note,
        }


class AutomaticEscalation:
    """Orkestrasi eskalasi (bukan engine baru — membungkus EscalationManager)."""

    def __init__(
        self, manager: Optional[EscalationManager] = None, ttl: int = 3600
    ) -> None:
        self._manager = manager or EscalationManager()
        self._ttl = ttl

    # --- memicu eskalasi ---

    async def escalate_for(
        self,
        *,
        ward_id: str,
        capability: str,
        reason: str,
        verdict: Optional[AuthorityVerdict] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EscalationRequest:
        """Buat escalation request ke manusia."""
        issue = f"{ward_id}:{capability} requires human decision"
        r = await self._manager.escalate(
            issue=issue,
            reason=reason,
            context=dict(context or {}),
        )
        # set TTL spesifik
        r.ttl = self._ttl
        return r

    # --- evaluasi keputusan manusia ---

    async def resolve(
        self, escalation_id: str, decision: str, note: str = ""
    ) -> EscalationOutcome:
        """Terapkan keputusan manusia atas escalation."""
        req = await self._manager.resolve_escalation(escalation_id, decision)
        if req is None:
            return EscalationOutcome(
                escalation_id=escalation_id, reason="", decided=False,
                note="not found",
            )
        approve = decision == DECISION_APPROVE
        reject = decision == DECISION_REJECT
        return EscalationOutcome(
            escalation_id=escalation_id,
            reason=req.reason,
            decided=True,
            approve=approve,
            reject=reject,
            note=note,
        )

    # --- helper keputusan loop ---

    @staticmethod
    def should_escalate(authority: AutonomousAuthority) -> bool:
        return authority.escalate or (
            authority.verdict == AuthorityVerdict.NO_AUTHORITY
        ) or (authority.verdict == AuthorityVerdict.BLOCKED)

    async def pending(self) -> list:
        return await self._manager.get_pending_escalations()

    async def manager(self) -> EscalationManager:
        return self._manager
