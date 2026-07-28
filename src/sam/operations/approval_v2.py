"""
Approval v2 — approval workflow yang lebih realistis.

State:
  Draft
  Waiting
  Approved
  ApprovedOnce
  ApprovedAlways
  Rejected
  Expired
  Cancelled

Action:
  Approve
  Reject
  ApproveOnce
  ApproveAlways
  Schedule
  Expire
  Escalate
  Cancel
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable
from datetime import datetime, timedelta
import enum


class ApprovalState(str, enum.Enum):
    DRAFT = "draft"
    WAITING = "waiting"
    APPROVED = "approved"
    APPROVED_ONCE = "approved_once"
    APPROVED_ALWAYS = "approved_always"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


VALID_TRANSITIONS = {
    ApprovalState.DRAFT: [ApprovalState.WAITING, ApprovalState.CANCELLED],
    ApprovalState.WAITING: [
        ApprovalState.APPROVED,
        ApprovalState.APPROVED_ONCE,
        ApprovalState.APPROVED_ALWAYS,
        ApprovalState.REJECTED,
        ApprovalState.EXPIRED,
        ApprovalState.ESCALATED,
        ApprovalState.CANCELLED,
    ],
    ApprovalState.APPROVED: [],             # terminal
    ApprovalState.APPROVED_ONCE: [],        # terminal
    ApprovalState.APPROVED_ALWAYS: [],      # terminal
    ApprovalState.REJECTED: [],             # terminal
    ApprovalState.EXPIRED: [],              # terminal
    ApprovalState.CANCELLED: [],            # terminal
    ApprovalState.ESCALATED: [ApprovalState.WAITING],  # can go back
}


@dataclass
class ApprovalV2Item:
    """Satu item approval dengan state management."""
    id: str
    title: str
    description: str = ""
    plan_id: str = ""
    source_decision_id: str = ""

    state: ApprovalState = ApprovalState.DRAFT
    state_history: List[str] = field(default_factory=list)

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    decided_at: str = ""
    decided_by: str = ""

    rejection_reason: str = ""
    escalation_note: str = ""
    schedule_at: str = ""

    expiry_minutes: int = 30

    can_approve: bool = True

    def is_terminal(self) -> bool:
        return self.state in (
            ApprovalState.APPROVED,
            ApprovalState.APPROVED_ONCE,
            ApprovalState.APPROVED_ALWAYS,
            ApprovalState.REJECTED,
            ApprovalState.EXPIRED,
            ApprovalState.CANCELLED,
        )

    def is_pending(self) -> bool:
        return self.state == ApprovalState.WAITING

    def is_expired(self) -> bool:
        if self.state != ApprovalState.WAITING:
            return False
        created = datetime.fromisoformat(self.created_at)
        elapsed = (datetime.now() - created).total_seconds() / 60
        return elapsed > self.expiry_minutes

    def transition_to(self, new_state: ApprovalState, decided_by: str = "",
                      reason: str = "") -> bool:
        """Pindah state — validasi dulu."""
        allowed = VALID_TRANSITIONS.get(self.state, [])
        if new_state not in allowed:
            return False

        self.state_history.append("{} -> {}".format(self.state.value, new_state.value))
        self.state = new_state
        self.updated_at = datetime.now().isoformat()

        if new_state in (
            ApprovalState.APPROVED,
            ApprovalState.APPROVED_ONCE,
            ApprovalState.APPROVED_ALWAYS,
            ApprovalState.REJECTED,
            ApprovalState.CANCELLED,
            ApprovalState.ESCALATED,
        ):
            self.decided_at = datetime.now().isoformat()
            self.decided_by = decided_by

        if new_state == ApprovalState.REJECTED:
            self.rejection_reason = reason
        elif new_state == ApprovalState.ESCALATED:
            self.escalation_note = reason
        elif new_state == ApprovalState.CANCELLED:
            self.rejection_reason = reason

        return True

    def approve(self, decided_by: str = "human") -> bool:
        return self.transition_to(ApprovalState.APPROVED, decided_by)

    def approve_once(self, decided_by: str = "human") -> bool:
        return self.transition_to(ApprovalState.APPROVED_ONCE, decided_by)

    def approve_always(self, decided_by: str = "human") -> bool:
        return self.transition_to(ApprovalState.APPROVED_ALWAYS, decided_by)

    def reject(self, reason: str = "", decided_by: str = "human") -> bool:
        return self.transition_to(ApprovalState.REJECTED, decided_by, reason)

    def escalate(self, note: str = "") -> bool:
        return self.transition_to(ApprovalState.ESCALATED, "system", note)

    def cancel(self, reason: str = "", decided_by: str = "system") -> bool:
        return self.transition_to(ApprovalState.CANCELLED, decided_by, reason)

    def summary_text(self) -> str:
        icon = {
            ApprovalState.WAITING: "PENDING",
            ApprovalState.APPROVED: "APPROVED",
            ApprovalState.APPROVED_ONCE: "APPROVED_ONCE",
            ApprovalState.APPROVED_ALWAYS: "APPROVED_ALWAYS",
            ApprovalState.REJECTED: "REJECTED",
            ApprovalState.EXPIRED: "EXPIRED",
            ApprovalState.CANCELLED: "CANCELLED",
            ApprovalState.ESCALATED: "ESCALATED",
        }.get(self.state, "UNKNOWN")
        return "[{icon}] {title} (by {by})".format(
            icon=icon, title=self.title,
            by=self.decided_by if self.decided_by else "?",
        )

    def to_text(self) -> str:
        lines = [
            "=== {} ===".format(self.title),
            "State: {} | ID: {}".format(self.state.value, self.id),
        ]
        if self.description:
            lines.append("Description: {}".format(self.description))
        if self.decided_by:
            lines.append("Decided: {} by {}".format(self.decided_at, self.decided_by))
        if self.rejection_reason:
            lines.append("Rejected: {}".format(self.rejection_reason))
        if self.escalation_note:
            lines.append("Escalated: {}".format(self.escalation_note))
        if self.state_history:
            lines.append("History: {}".format(" -> ".join(self.state_history)))
        return "\n".join(lines)


class ApprovalV2Workflow:
    """Workflow approval v2 dengan state management."""

    def __init__(self):
        self._items: List[ApprovalV2Item] = []
        self._id_counter: int = 0

    def submit(self, title: str, description: str = "",
               plan_id: str = "", source_decision_id: str = "") -> ApprovalV2Item:
        """Submit baru — langsung WAITING."""
        self._id_counter += 1
        item = ApprovalV2Item(
            id="ap-{:04d}".format(self._id_counter),
            title=title,
            description=description,
            plan_id=plan_id,
            source_decision_id=source_decision_id,
            state=ApprovalState.WAITING,
            state_history=["-> waiting"],
        )
        self._items.append(item)
        return item

    def submit_from_plan(self, plan) -> ApprovalV2Item:
        """Submit dari ExecutionPlan."""
        return self.submit(
            title=plan.source_decision_title or plan.plan_id,
            description="Execution plan with {} action(s)".format(len(plan.actions)),
            plan_id=plan.plan_id,
        )

    def approve(self, item_id: str, decided_by: str = "human") -> bool:
        item = self._get(item_id)
        return item.approve(decided_by) if item else False

    def approve_once(self, item_id: str, decided_by: str = "human") -> bool:
        item = self._get(item_id)
        return item.approve_once(decided_by) if item else False

    def approve_always(self, item_id: str, decided_by: str = "human") -> bool:
        item = self._get(item_id)
        return item.approve_always(decided_by) if item else False

    def reject(self, item_id: str, reason: str = "", decided_by: str = "human") -> bool:
        item = self._get(item_id)
        return item.reject(reason, decided_by) if item else False

    def escalate(self, item_id: str, note: str = "") -> bool:
        item = self._get(item_id)
        return item.escalate(note) if item else False

    def cancel(self, item_id: str, reason: str = "") -> bool:
        item = self._get(item_id)
        return item.cancel(reason) if item else False

    def expire(self, item_id: str) -> bool:
        item = self._get(item_id)
        if item and item.is_expired():
            return item.transition_to(ApprovalState.EXPIRED, "system")
        return False

    def get_pending(self) -> List[ApprovalV2Item]:
        self._expire_all()
        return [i for i in self._items if i.is_pending()]

    def get_history(self, limit: int = 20) -> List[ApprovalV2Item]:
        decided = [i for i in self._items if i.is_terminal()]
        decided.sort(key=lambda x: x.updated_at, reverse=True)
        return decided[:limit]

    def get_all(self) -> List[ApprovalV2Item]:
        return self._items

    def get_by_state(self, state: ApprovalState) -> List[ApprovalV2Item]:
        return [i for i in self._items if i.state == state]

    def _get(self, item_id: str) -> Optional[ApprovalV2Item]:
        for i in self._items:
            if i.id == item_id:
                return i
        return None

    def _expire_all(self):
        for item in self._items:
            if item.is_expired():
                item.transition_to(ApprovalState.EXPIRED, "system")
