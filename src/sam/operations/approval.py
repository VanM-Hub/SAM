"""
ApprovalWorkflow — Siklus hidup approval keputusan.

Status siklus hidup:
  Draft → Waiting Approval → Approved / Rejected / Expired

Belum ada execution.
Hanya mengelola approval state.
Semua keputusan harus melalui approval sebelum dieksekusi (placeholder).
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta
import json
import os


DEFAULT_EXPIRY_MINUTES = 30


class ApprovalStatus:
    DRAFT = "draft"
    WAITING = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalItem:
    """Satu item approval dengan siklus hidup."""
    id: str
    decision: str
    reason: str
    confidence: float

    # Evidence
    evidence: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    uncertainty: str = ""

    # Impact
    expected_outcome: str = ""
    risk: str = ""
    possible_interruption: str = ""
    estimated_recovery: str = ""

    # Alternatives
    alternative: str = ""
    emergency: str = ""

    # Workflow
    status: str = ApprovalStatus.DRAFT
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    decided_at: str = ""
    decided_by: str = ""
    rejection_reason: str = ""
    expiry_minutes: int = DEFAULT_EXPIRY_MINUTES

    def is_expired(self) -> bool:
        if self.status != ApprovalStatus.WAITING:
            return False
        created = datetime.fromisoformat(self.created_at)
        elapsed = (datetime.now() - created).total_seconds() / 60
        return elapsed > self.expiry_minutes

    def summary_text(self) -> str:
        """Ringkasan untuk Action Center."""
        status_icon = {
            ApprovalStatus.DRAFT: "📝",
            ApprovalStatus.WAITING: "⏳",
            ApprovalStatus.APPROVED: "✅",
            ApprovalStatus.REJECTED: "❌",
            ApprovalStatus.EXPIRED: "⌛",
        }.get(self.status, "❓")
        return "{icon} **{decision}** — Confidence: {conf:.0f}% | Risk: {risk} | {status}".format(
            icon=status_icon,
            decision=self.decision,
            conf=self.confidence * 100,
            risk=self.risk or "Unknown",
            status=self.status,
        )

    def to_text(self) -> str:
        lines = []
        lines.append("=== {} ===".format(self.decision))
        lines.append("Status: {} | Confidence: {:.0f}%".format(self.status, self.confidence * 100))
        lines.append("Reason: {}".format(self.reason))
        if self.expected_outcome:
            lines.append("Expected: {}".format(self.expected_outcome))
        if self.risk:
            lines.append("Risk: {}".format(self.risk))
        if self.possible_interruption:
            lines.append("Interruption: {}".format(self.possible_interruption))
        if self.estimated_recovery:
            lines.append("Recovery: {}".format(self.estimated_recovery))
        if self.evidence:
            lines.append("Evidence ({}):".format(len(self.evidence)))
            for e in self.evidence[:3]:
                lines.append("  - {}".format(e))
        if self.missing_information:
            lines.append("Missing:")
            for m in self.missing_information[:2]:
                lines.append("  - {}".format(m))
        if self.alternative:
            lines.append("Alternative: {}".format(self.alternative))
        if self.emergency:
            lines.append("Emergency: {}".format(self.emergency))
        if self.decided_at:
            lines.append("Decided: {} by {}".format(self.decided_at, self.decided_by))
        if self.rejection_reason:
            lines.append("Rejected: {}".format(self.rejection_reason))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "decision": self.decision,
            "reason": self.reason,
            "confidence": self.confidence,
            "status": self.status,
            "risk": self.risk,
            "evidence": self.evidence,
            "missing_information": self.missing_information,
            "uncertainty": self.uncertainty,
            "expected_outcome": self.expected_outcome,
            "possible_interruption": self.possible_interruption,
            "estimated_recovery": self.estimated_recovery,
            "alternative": self.alternative,
            "emergency": self.emergency,
            "created_at": self.created_at,
            "decided_at": self.decided_at,
            "decided_by": self.decided_by,
            "rejection_reason": self.rejection_reason,
        }


class ApprovalStore:
    """Penyimpanan approval — file-based JSON.

    Menggunakan file JSON sederhana untuk persistensi.
    Lokasi: workspace/approvals.json atau custom path.
    """

    def __init__(self, path: Optional[str] = None):
        if path:
            self._path = path
        else:
            base = os.environ.get("SAM_WORKSPACE", os.getcwd())
            self._path = os.path.join(base, "approvals.json")
        self._items: List[ApprovalItem] = []

    def load(self):
        """Load approval items dari file."""
        if os.path.exists(self._path):
            try:
                with open(self._path, "r") as f:
                    data = json.load(f)
                self._items = [ApprovalItem(**item) for item in data]
            except (json.JSONDecodeError, IOError):
                self._items = []
        else:
            self._items = []

    def save(self):
        """Simpan approval items ke file."""
        try:
            with open(self._path, "w") as f:
                json.dump([item.to_dict() for item in self._items], f, indent=2)
        except IOError:
            pass  # Save silently fails — data still in memory

    def add(self, item: ApprovalItem):
        """Tambah item baru."""
        self._items.append(item)
        self.save()

    def get_all(self) -> List[ApprovalItem]:
        """Semua item."""
        return self._items

    def get_by_status(self, status: str) -> List[ApprovalItem]:
        """Filter by status."""
        return [i for i in self._items if i.status == status]

    def get_by_id(self, item_id: str) -> Optional[ApprovalItem]:
        """Cari by id."""
        for i in self._items:
            if i.id == item_id:
                return i
        return None

    def update_status(self, item_id: str, new_status: str,
                      decided_by: str = "",
                      rejection_reason: str = "") -> bool:
        """Update status item."""
        item = self.get_by_id(item_id)
        if item is None:
            return False
        item.status = new_status
        if new_status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED):
            item.decided_at = datetime.now().isoformat()
            item.decided_by = decided_by
        if new_status == ApprovalStatus.REJECTED:
            item.rejection_reason = rejection_reason
        self.save()
        return True

    def remove_expired(self):
        """Tandai expired items."""
        now = datetime.now()
        for item in self._items:
            if item.status == ApprovalStatus.WAITING and item.is_expired():
                item.status = ApprovalStatus.EXPIRED
                item.decided_at = now.isoformat()
                item.decided_by = "system"
        self.save()

    def get_pending_count(self) -> int:
        """Jumlah item yang menunggu approval."""
        self.remove_expired()
        return len(self.get_by_status(ApprovalStatus.WAITING))


class ApprovalWorkflow:
    """Workflow approval untuk keputusan.

    Mengelola: Draft → Waiting Approval → Approved/Rejected/Expired.
    """

    def __init__(self, store: Optional[ApprovalStore] = None):
        self._store = store or ApprovalStore()
        self._store.load()

    @property
    def store(self) -> ApprovalStore:
        return self._store

    # ====================================================================
    # Submit
    # ====================================================================

    def submit(self, decision: str, reason: str, confidence: float,
               evidence: List[str] = None,
               missing_information: List[str] = None,
               uncertainty: str = "",
               expected_outcome: str = "",
               risk: str = "",
               possible_interruption: str = "",
               estimated_recovery: str = "",
               alternative: str = "",
               emergency: str = "") -> ApprovalItem:
        """Kirim keputusan ke approval workflow.

        Status langsung → WAITING.
        """
        if evidence is None:
            evidence = []
        if missing_information is None:
            missing_information = []

        item = ApprovalItem(
            id=self._next_id(),
            decision=decision,
            reason=reason,
            confidence=confidence,
            evidence=evidence,
            missing_information=missing_information,
            uncertainty=uncertainty,
            expected_outcome=expected_outcome,
            risk=risk,
            possible_interruption=possible_interruption,
            estimated_recovery=estimated_recovery,
            alternative=alternative,
            emergency=emergency,
            status=ApprovalStatus.WAITING,
        )
        self._store.add(item)
        return item

    def submit_from_proposal(self, proposal) -> Optional[ApprovalItem]:
        """Kirim DecisionProposal ke approval workflow."""
        return self.submit(
            decision=proposal.decision,
            reason=proposal.reason,
            confidence=proposal.confidence,
            evidence=proposal.required_evidence,
            missing_information=proposal.missing_information,
            uncertainty=proposal.uncertainty,
        )

    def submit_all(self, proposals) -> List[ApprovalItem]:
        """Kirim semua proposal ke approval workflow."""
        items = []
        if hasattr(proposals, 'proposals'):
            prop_list = proposals.proposals
        else:
            prop_list = proposals
        for p in prop_list:
            item = self.submit_from_proposal(p)
            if item:
                items.append(item)
        return items

    # ====================================================================
    # Approve / Reject
    # ====================================================================

    def approve(self, item_id: str, decided_by: str = "human") -> bool:
        """Setujui keputusan."""
        result = self._store.update_status(item_id, ApprovalStatus.APPROVED, decided_by=decided_by)
        if result:
            self._store.save()
        return result

    def reject(self, item_id: str, reason: str = "", decided_by: str = "human") -> bool:
        """Tolak keputusan."""
        result = self._store.update_status(
            item_id, ApprovalStatus.REJECTED,
            decided_by=decided_by,
            rejection_reason=reason,
        )
        if result:
            self._store.save()
        return result

    # ====================================================================
    # Query
    # ====================================================================

    def get_pending(self) -> List[ApprovalItem]:
        """Keputusan yang menunggu approval."""
        self._store.remove_expired()
        return self._store.get_by_status(ApprovalStatus.WAITING)

    def get_approved(self) -> List[ApprovalItem]:
        """Keputusan yang sudah disetujui."""
        return self._store.get_by_status(ApprovalStatus.APPROVED)

    def get_rejected(self) -> List[ApprovalItem]:
        """Keputusan yang ditolak."""
        return self._store.get_by_status(ApprovalStatus.REJECTED)

    def get_history(self, limit: int = 20) -> List[ApprovalItem]:
        """Riwayat approval — yang sudah diputuskan."""
        self._store.remove_expired()
        decided = [i for i in self._store.get_all()
                   if i.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED)]
        decided.sort(key=lambda x: x.decided_at, reverse=True)
        return decided[:limit]

    # ====================================================================
    # Internal
    # ====================================================================

    def _next_id(self) -> str:
        """Generate unique ID."""
        import uuid
        return uuid.uuid4().hex[:12]
