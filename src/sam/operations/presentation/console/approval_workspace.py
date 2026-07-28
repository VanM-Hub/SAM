"""ApprovalWorkspace — Approval workspace for the SAM Console.

Operator can view pending approvals, approve, reject with reason,
and view approval history. All actions go through Conversation API
via the Interaction Contract.

No business logic. No direct storage access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class ApprovalItem:
    """A single approval request (immutable)."""
    request_id: str
    title: str
    description: str
    requester: str
    mission_id: str = ""
    priority: str = "normal"  # critical, high, normal, low
    status: str = "pending"   # pending, approved, rejected, expired
    created_at: str = ""
    decided_by: str = ""
    decided_at: str = ""
    reason: str = ""


@dataclass(frozen=True)
class ApprovalWorkspace:
    """Approval workspace view model.

    Pure data. Actions go through Conversation API.
    """

    pending: Tuple[ApprovalItem, ...] = ()
    history: Tuple[ApprovalItem, ...] = ()
    total_pending: int = 0
    total_history: int = 0
    critical_pending: int = 0

    def by_status(self, status: str) -> ApprovalWorkspace:
        if status == "pending":
            return ApprovalWorkspace(
                pending=self.pending, history=(),
                total_pending=self.total_pending,
                critical_pending=self.critical_pending,
            )
        elif status == "history":
            return ApprovalWorkspace(
                pending=(), history=self.history,
                total_history=self.total_history,
            )
        return self

    @property
    def summary_line(self) -> str:
        return (
            f"Approvals: {self.total_pending} pending "
            f"({self.critical_pending} critical), "
            f"{self.total_history} in history"
        )


@dataclass(frozen=True)
class ApprovalAction:
    """Result of an approval action (approve/reject).

    Does NOT execute the action itself — just models the result.
    Execution happens through the Conversation API.
    """
    request_id: str
    action: str  # approved, rejected
    success: bool
    message: str = ""


@dataclass(frozen=True)
class ApprovalDispatcher:
    """Routes approval actions to the Conversation API.

    Builds the command string. Does NOT execute business logic.
    """

    @staticmethod
    def build_approve(
        request_id: str, reason: str = "",
    ) -> Tuple[str, Dict[str, str]]:
        """Build approve command and params.

        Returns (command_name, params_dict).
        """
        return ("approve", {
            "id": request_id,
            "reason": reason,
        })

    @staticmethod
    def build_reject(
        request_id: str, reason: str = "",
    ) -> Tuple[str, Dict[str, str]]:
        """Build reject command and params."""
        return ("reject", {
            "id": request_id,
            "reason": reason,
        })

    @staticmethod
    def build_review_history(
        limit: int = 20,
    ) -> Tuple[str, Dict[str, str]]:
        """Build command to fetch approval history."""
        return ("history", {"limit": str(limit)})


# ── Factory ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ApprovalWorkspaceFactory:
    """Creates ApprovalWorkspace from raw data.

    Translates ActionCenterDTO or dict data into ApprovalItem entries.
    """

    @staticmethod
    def from_action_center(dto: object) -> ApprovalWorkspace:
        """Build from ActionCenterDTO."""
        if dto is None:
            return ApprovalWorkspace()

        pending_count = getattr(dto, 'pending_approvals', 0)
        total_pending = getattr(dto, 'total_pending', pending_count)
        critical_pending = getattr(dto, 'critical_pending', 0)

        # Parse approval items if available
        items = getattr(dto, 'pending_approvals', ())
        pending_items: List[ApprovalItem] = []

        if isinstance(items, (tuple, list)):
            for item in items:
                if isinstance(item, dict):
                    pending_items.append(_parse_approval_item(item))

        return ApprovalWorkspace(
            pending=tuple(pending_items),
            total_pending=total_pending or pending_count,
            critical_pending=critical_pending,
        )

    @staticmethod
    def from_dicts(
        pending: List[dict] = None,
        history: List[dict] = None,
    ) -> ApprovalWorkspace:
        """Build from dict lists."""
        pending_items: List[ApprovalItem] = []
        history_items: List[ApprovalItem] = []
        critical = 0

        for item in (pending or []):
            parsed = _parse_approval_item(item)
            pending_items.append(parsed)
            if parsed.priority == "critical":
                critical += 1

        for item in (history or []):
            history_items.append(_parse_approval_item(item))

        return ApprovalWorkspace(
            pending=tuple(pending_items),
            history=tuple(history_items),
            total_pending=len(pending_items),
            total_history=len(history_items),
            critical_pending=critical,
        )

    @staticmethod
    def empty() -> ApprovalWorkspace:
        return ApprovalWorkspace()


def _parse_approval_item(data: dict) -> ApprovalItem:
    return ApprovalItem(
        request_id=str(data.get('request_id', data.get('id', ''))),
        title=str(data.get('title', '')),
        description=str(data.get('description', '')),
        requester=str(data.get('requester', 'system')),
        mission_id=str(data.get('mission_id', '')),
        priority=str(data.get('priority', 'normal')),
        status=str(data.get('status', 'pending')),
        created_at=str(data.get('created_at', '')),
        decided_by=str(data.get('decided_by', '')),
        decided_at=str(data.get('decided_at', '')),
        reason=str(data.get('reason', '')),
    )
