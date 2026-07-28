"""
OP-256 — Proposal Queue.

Priority queue for MissionProposals waiting for approval.
Queue is in front of Approval: Proposal -> Queue -> Approval -> Mission.

Proposals expire if not approved within TTL.
Expired proposals are NOT deleted — preserved for audit.
Supports Draft -> Ready -> Waiting -> Approved/Rejected/Expired lifecycle.
"""

from __future__ import annotations

import time
import heapq
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProposalState(Enum):
    """Lifecycle states of a queued proposal."""

    DRAFT = "draft"
    READY = "ready"
    WAITING = "waiting"  # submitted to approval
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


_VALID_TRANSITIONS: Dict[ProposalState, set] = {
    ProposalState.DRAFT: {ProposalState.READY, ProposalState.EXPIRED},
    ProposalState.READY: {ProposalState.WAITING, ProposalState.DRAFT, ProposalState.EXPIRED},
    ProposalState.WAITING: {ProposalState.APPROVED, ProposalState.REJECTED, ProposalState.EXPIRED},
    ProposalState.APPROVED: set(),
    ProposalState.REJECTED: set(),
    ProposalState.EXPIRED: set(),
}


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        item_id: str,
        from_state: ProposalState,
        to_state: ProposalState,
    ) -> None:
        super().__init__(
            f"Cannot transition {item_id} from "
            f"{from_state.value} to {to_state.value}"
        )


@dataclass
class QueueItem:
    """An item in the proposal queue."""

    proposal_id: str
    title: str
    priority_score: float
    state: ProposalState
    created_at: float
    ttl_seconds: float = 86400.0  # default 24h
    updated_at: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if this item has exceeded its TTL."""
        return (time.time() - self.created_at) > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at

    def __repr__(self) -> str:
        return (
            f"QueueItem({self.proposal_id[:8]}...: "
            f"priority={self.priority_score:.0f}, "
            f"state={self.state.value})"
        )

    # ── Heap ordering (lower priority_score = higher priority) ─────

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, QueueItem):
            return NotImplemented
        # Primary: priority score (higher = more urgent)
        if abs(self.priority_score - other.priority_score) > 0.01:
            return self.priority_score > other.priority_score
        # Secondary: older first
        return self.created_at < other.created_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QueueItem):
            return NotImplemented
        return self.proposal_id == other.proposal_id

    def __hash__(self) -> int:
        return hash(self.proposal_id)


class ProposalQueue:
    """Priority queue for proposals waiting for approval.

    Ordering: Highest priority_score first, then oldest first.
    Supports expiration, state machine, and audit trail.
    """

    def __init__(self) -> None:
        self._items: Dict[str, QueueItem] = {}
        self._heap: List[QueueItem] = []
        self._history: List[QueueItem] = []

    # ── Properties ─────────────────────────────────────────────────

    @property
    def size(self) -> int:
        """Number of active items (not approved/rejected/expired)."""
        return len(self._items)

    @property
    def waiting_count(self) -> int:
        """Number of items in WAITING state."""
        return sum(
            1 for i in self._items.values()
            if i.state == ProposalState.WAITING
        )

    @property
    def ready_count(self) -> int:
        return sum(
            1 for i in self._items.values()
            if i.state == ProposalState.READY
        )

    @property
    def draft_count(self) -> int:
        return sum(
            1 for i in self._items.values()
            if i.state == ProposalState.DRAFT
        )

    # ── CRUD ───────────────────────────────────────────────────────

    def push(
        self,
        proposal_id: str,
        title: str,
        priority_score: float,
        ttl_seconds: float = 86400.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QueueItem:
        """Add a new proposal to the queue as DRAFT."""
        item = QueueItem(
            proposal_id=proposal_id,
            title=title,
            priority_score=priority_score,
            state=ProposalState.DRAFT,
            created_at=time.time(),
            updated_at=time.time(),
            ttl_seconds=ttl_seconds,
            metadata=metadata or {},
        )
        self._items[proposal_id] = item
        heapq.heappush(self._heap, item)
        return item

    def get(self, proposal_id: str) -> Optional[QueueItem]:
        return self._items.get(proposal_id)

    def remove(self, proposal_id: str) -> bool:
        """Remove an item from active queue (moves to history)."""
        item = self._items.pop(proposal_id, None)
        if item is None:
            return False
        self._history.append(item)
        return True

    # ── State transitions ──────────────────────────────────────────

    def _transition(
        self,
        proposal_id: str,
        target: ProposalState,
    ) -> QueueItem:
        """Apply state transition with validation."""
        item = self._items.get(proposal_id)
        if item is None:
            raise ValueError(f"Unknown proposal: {proposal_id}")

        if target not in _VALID_TRANSITIONS.get(item.state, set()):
            raise InvalidTransitionError(proposal_id, item.state, target)

        # Mutate (we own the dict, safe to use object.__setattr__)
        object.__setattr__(item, "state", target)
        object.__setattr__(item, "updated_at", time.time())

        # If terminal state, move to history
        if target in (
            ProposalState.APPROVED,
            ProposalState.REJECTED,
            ProposalState.EXPIRED,
        ):
            self._items.pop(proposal_id, None)
            self._history.append(item)

        return item

    def mark_ready(self, proposal_id: str) -> QueueItem:
        """Move from DRAFT -> READY."""
        return self._transition(proposal_id, ProposalState.READY)

    def mark_waiting(self, proposal_id: str) -> QueueItem:
        """Move from READY -> WAITING.

        Forwards to approval system.
        """
        item = self._transition(proposal_id, ProposalState.WAITING)
        self._forward_to_approval(item)
        return item

    def approve(self, proposal_id: str) -> QueueItem:
        """Mark as APPROVED."""
        return self._transition(proposal_id, ProposalState.APPROVED)

    def reject(self, proposal_id: str) -> QueueItem:
        """Mark as REJECTED."""
        return self._transition(proposal_id, ProposalState.REJECTED)

    def expire(self, proposal_id: str) -> QueueItem:
        """Mark as EXPIRED."""
        return self._transition(proposal_id, ProposalState.EXPIRED)

    # ── Queue operations ───────────────────────────────────────────

    def pop_ready(self) -> Optional[QueueItem]:
        """Pop the highest-priority READY item for approval."""
        # Rebuild heap to ensure consistency
        self._rebuild()
        while self._heap:
            item = self._heap[0]
            if item.proposal_id not in self._items:
                heapq.heappop(self._heap)
                continue
            if item.state != ProposalState.READY:
                heapq.heappop(self._heap)
                continue
            heapq.heappop(self._heap)
            return self.mark_waiting(item.proposal_id)
        return None

    def peek(self) -> Optional[QueueItem]:
        """View highest-priority item without popping."""
        self._rebuild()
        while self._heap:
            item = self._heap[0]
            if item.proposal_id not in self._items:
                heapq.heappop(self._heap)
                continue
            return item
        return None

    def list_ready(self) -> List[QueueItem]:
        """List all READY items sorted by priority."""
        return sorted(
            [i for i in self._items.values() if i.state == ProposalState.READY],
            key=lambda i: (-i.priority_score, i.created_at),
        )

    def list_active(self) -> List[QueueItem]:
        """List all active items sorted by priority."""
        return sorted(
            self._items.values(),
            key=lambda i: (-i.priority_score, i.created_at),
        )

    def list_history(
        self,
        limit: int = 50,
    ) -> List[QueueItem]:
        """List historical (terminal) items, newest first."""
        return sorted(
            self._history,
            key=lambda i: i.updated_at,
            reverse=True,
        )[:limit]

    # ── Expiration ─────────────────────────────────────────────────

    def expire_stale(self) -> int:
        """Expire all items past their TTL.

        Returns count of expired items.
        """
        now = time.time()
        expired_count = 0
        for item in list(self._items.values()):
            if (now - item.created_at) > item.ttl_seconds:
                try:
                    self.expire(item.proposal_id)
                    expired_count += 1
                except (InvalidTransitionError, ValueError):
                    continue
        return expired_count

    # ── Internal ───────────────────────────────────────────────────

    def _rebuild(self) -> None:
        """Rebuild heap from active items."""
        self._heap = [i for i in self._heap if i.proposal_id in self._items]
        heapq.heapify(self._heap)

    @staticmethod
    def _forward_to_approval(item: QueueItem) -> None:
        """Forward a waiting proposal to the approval system."""
        try:
            from sam.operations.approval import queue_approval
            queue_approval(
                item_type="brain_proposal",
                item_id=item.proposal_id,
                item_summary=item.title,
                requires_approval=True,
            )
        except Exception:
            pass  # graceful fallback

    def __repr__(self) -> str:
        return (
            f"ProposalQueue(size={self.size}, "
            f"ready={self.ready_count}, "
            f"waiting={self.waiting_count})"
        )


# ── Convenience ───────────────────────────────────────────────────────


def create_draft(
    proposal_id: str,
    title: str,
    priority_score: float,
    queue: Optional[ProposalQueue] = None,
) -> QueueItem:
    """Create a draft proposal in the queue."""
    q = queue or ProposalQueue()
    return q.push(proposal_id, title, priority_score)
