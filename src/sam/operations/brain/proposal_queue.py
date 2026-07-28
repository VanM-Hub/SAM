"""
OP-256 — Proposal Queue.

Manages the lifecycle of proposals:
  draft → ready → waiting_approval → approved | rejected | expired

States:
  - draft: being prepared, not yet visible
  - ready: prepared and visible, pending submission
  - waiting_approval: submitted, awaiting operator decision
  - approved: operator approved → ready for execution
  - rejected: operator rejected
  - expired: timed out before decision

Transitions:
  draft -> ready (finalize)
  ready -> waiting_approval (submit)
  waiting_approval -> approved (approve)
  waiting_approval -> rejected (reject)
  waiting_approval -> expired (timeout)
  approved -> completed (mission created)
  rejected -> archived
  expired -> archived
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ── Types ──────────────────────────────────────────────────────────


class ProposalState(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    COMPLETED = "completed"
    ARCHIVED = "archived"


VALID_TRANSITIONS: Dict[ProposalState, Set[ProposalState]] = {
    ProposalState.DRAFT: {ProposalState.READY},
    ProposalState.READY: {ProposalState.WAITING_APPROVAL},
    ProposalState.WAITING_APPROVAL: {ProposalState.APPROVED,
                                      ProposalState.REJECTED,
                                      ProposalState.EXPIRED},
    ProposalState.APPROVED: {ProposalState.COMPLETED},
    ProposalState.REJECTED: {ProposalState.ARCHIVED},
    ProposalState.EXPIRED: {ProposalState.ARCHIVED},
    ProposalState.COMPLETED: set(),
    ProposalState.ARCHIVED: set(),
}


@dataclass
class QueueItem:
    """A proposal in the queue."""

    proposal_id: str
    state: ProposalState
    title: str
    description: str
    created_at: float
    updated_at: float
    ttl_seconds: Optional[float] = None  # auto-expire after this many seconds
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    package_id: Optional[str] = None
    reason: Optional[str] = None  # approval/rejection reason
    priority_score: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.state in (
            ProposalState.COMPLETED,
            ProposalState.ARCHIVED,
        )

    @property
    def is_pending(self) -> bool:
        return self.state in (
            ProposalState.DRAFT,
            ProposalState.READY,
            ProposalState.WAITING_APPROVAL,
        )

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


# ── Errors ─────────────────────────────────────────────────────────


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, item_id: str, from_state: ProposalState, to_state: ProposalState):
        super().__init__(
            f"Cannot transition {item_id} from {from_state.value} to {to_state.value}"
        )
        self.item_id = item_id
        self.from_state = from_state
        self.to_state = to_state


# ── Queue ──────────────────────────────────────────────────────────


class ProposalQueue:
    """
    Manages the full lifecycle of proposals.

    Thread-safe via simple lock for critical sections.
    """

    def __init__(self, default_ttl: Optional[float] = 3600.0):  # 1 hour
        self._items: Dict[str, QueueItem] = {}
        self._default_ttl = default_ttl
        self._on_transition: Dict[str, List[Callable]] = {}

    # ── Public API ─────────────────────────────────────────────────

    @property
    def count(self) -> int:
        return len(self._items)

    def add(self, title: str, description: str = "",
            evidence: Optional[List[Dict[str, Any]]] = None,
            priority_score: float = 0.5,
            ttl_seconds: Optional[float] = None,
            metadata: Optional[Dict[str, Any]] = None,
            proposal_id: Optional[str] = None) -> QueueItem:
        """Add a new proposal in DRAFT state."""
        pid = proposal_id or f"prop_{uuid.uuid4().hex[:12]}"
        item = QueueItem(
            proposal_id=pid,
            state=ProposalState.DRAFT,
            title=title,
            description=description,
            created_at=time.time(),
            updated_at=time.time(),
            ttl_seconds=ttl_seconds or self._default_ttl,
            evidence=evidence or [],
            priority_score=priority_score,
            metadata=metadata or {},
        )
        self._items[pid] = item
        return item

    def get(self, proposal_id: str) -> Optional[QueueItem]:
        return self._items.get(proposal_id)

    def remove(self, proposal_id: str) -> bool:
        return self._items.pop(proposal_id, None) is not None

    def transition(self, proposal_id: str, to_state: ProposalState,
                   reason: Optional[str] = None) -> QueueItem:
        """
        Transition a proposal to a new state.

        Raises InvalidTransitionError if disallowed.
        """
        item = self._items.get(proposal_id)
        if item is None:
            raise ValueError(f"Proposal not found: {proposal_id}")

        if to_state not in VALID_TRANSITIONS.get(item.state, set()):
            raise InvalidTransitionError(proposal_id, item.state, to_state)

        item.state = to_state
        item.updated_at = time.time()
        if reason:
            item.reason = reason

        self._fire_callbacks(proposal_id, item.state)
        return item

    def finalize(self, proposal_id: str) -> QueueItem:
        """DRAFT -> READY."""
        return self.transition(proposal_id, ProposalState.READY)

    def submit(self, proposal_id: str) -> QueueItem:
        """READY -> WAITING_APPROVAL."""
        return self.transition(proposal_id, ProposalState.WAITING_APPROVAL)

    def approve(self, proposal_id: str, reason: Optional[str] = None) -> QueueItem:
        """WAITING_APPROVAL -> APPROVED."""
        return self.transition(proposal_id, ProposalState.APPROVED, reason)

    def reject(self, proposal_id: str, reason: Optional[str] = None) -> QueueItem:
        """WAITING_APPROVAL -> REJECTED."""
        return self.transition(proposal_id, ProposalState.REJECTED, reason)

    def complete(self, proposal_id: str) -> QueueItem:
        """APPROVED -> COMPLETED."""
        return self.transition(proposal_id, ProposalState.COMPLETED)

    def archive(self, proposal_id: str) -> QueueItem:
        """REJECTED/EXPIRED -> ARCHIVED."""
        item = self._items.get(proposal_id)
        if item and item.state in (ProposalState.REJECTED, ProposalState.EXPIRED):
            return self.transition(proposal_id, ProposalState.ARCHIVED)
        raise ValueError(f"Cannot archive {proposal_id}: state must be rejected or expired")

    # ── Query ──────────────────────────────────────────────────────

    def list_by_state(self, *states: ProposalState) -> List[QueueItem]:
        """List all items in given states."""
        return [item for item in self._items.values()
                if item.state in states]

    def list_pending(self) -> List[QueueItem]:
        """DRAFT + READY + WAITING_APPROVAL."""
        return self.list_by_state(
            ProposalState.DRAFT,
            ProposalState.READY,
            ProposalState.WAITING_APPROVAL,
        )

    def list_waiting(self) -> List[QueueItem]:
        """Items awaiting operator decision."""
        return self.list_by_state(ProposalState.WAITING_APPROVAL)

    def list_ready(self) -> List[QueueItem]:
        """Items in READY state (prepared but not submitted)."""
        return self.list_by_state(ProposalState.READY)

    def list_approved(self) -> List[QueueItem]:
        return self.list_by_state(ProposalState.APPROVED)

    def list_by_package(self, package_id: str) -> List[QueueItem]:
        return [item for item in self._items.values()
                if item.package_id == package_id]

    def get_pending_count(self) -> int:
        return len(self.list_pending())

    def get_waiting_count(self) -> int:
        return len(self.list_waiting())

    # ── Maintenance ────────────────────────────────────────────────

    def expire_stale(self) -> int:
        """
        Expire proposals in WAITING_APPROVAL that exceed their TTL.
        Returns count of expired items.
        """
        now = time.time()
        expired = 0
        for item in list(self._items.values()):
            if item.state != ProposalState.WAITING_APPROVAL:
                continue
            if item.ttl_seconds is None:
                continue
            age = now - item.updated_at
            if age > item.ttl_seconds:
                try:
                    self.transition(item.proposal_id, ProposalState.EXPIRED,
                                    reason="TTL expired")
                    expired += 1
                except InvalidTransitionError:
                    pass
        return expired

    def cleanup_archived(self, max_age: float = 86400.0) -> int:
        """Remove archived items older than max_age seconds."""
        now = time.time()
        to_remove = []
        for item in self._items.values():
            if item.state != ProposalState.ARCHIVED:
                continue
            if now - item.updated_at > max_age:
                to_remove.append(item.proposal_id)
        for pid in to_remove:
            self.remove(pid)
        return len(to_remove)

    # ── Events / Callbacks ─────────────────────────────────────────

    def on_transition(self, state: ProposalState,
                      callback: Callable[[str, ProposalState], None]) -> None:
        """Register a callback for state transitions to a specific state."""
        key = state.value
        if key not in self._on_transition:
            self._on_transition[key] = []
        self._on_transition[key].append(callback)

    def _fire_callbacks(self, proposal_id: str, state: ProposalState) -> None:
        key = state.value
        for cb in self._on_transition.get(key, []):
            try:
                cb(proposal_id, state)
            except Exception:
                pass


# ── Convenience ────────────────────────────────────────────────────


def create_draft(title: str, **kwargs) -> QueueItem:
    """One-shot: create a draft proposal."""
    queue = ProposalQueue()
    return queue.add(title=title, **kwargs)
