# OP-424 — Dispatch Queue
# Python 3.8, frozen DTO, synchronous, no worker thread

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .dispatch_request import (
    DispatchRequest, DispatchStatus, DispatchPriority, DispatchMetadata,
)


@dataclass(frozen=True)
class QueuedDispatch:
    queue_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    priority: DispatchPriority = field(default_factory=DispatchPriority.normal)
    enqueued_at: datetime = field(default_factory=datetime.utcnow)
    status: DispatchStatus = field(default_factory=DispatchStatus.queued)
    retry_count: int = 0


@dataclass(frozen=True)
class DispatchBatchQueue:
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    items: Tuple[QueuedDispatch, ...] = field(default_factory=tuple)
    total: int = 0
    status: str = "pending"


@dataclass(frozen=True)
class QueueStatistics:
    total_queued: int = 0
    pending: int = 0
    dispatched: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    avg_priority: float = 0.0
    estimated_wait_seconds: int = 0


class DispatchQueue:
    """In-memory dispatch queue.

    Supports enqueue, dequeue, cancel, reorder, priority.
    No worker thread — purely synchronous operations.
    """

    def __init__(self) -> None:
        self._items: Dict[str, QueuedDispatch] = {}
        self._requests: Dict[str, DispatchRequest] = {}

    def enqueue(self, request: DispatchRequest) -> QueuedDispatch:
        """Add a dispatch request to the queue."""
        qd = QueuedDispatch(
            request_id=request.request_id,
            priority=request.priority,
        )
        self._items[qd.queue_id] = qd
        self._requests[request.request_id] = request.with_status(
            DispatchStatus.queued()
        )
        return qd

    def dequeue(self) -> Optional[Tuple[QueuedDispatch, DispatchRequest]]:
        """Dequeue the highest-priority item."""
        if not self._items:
            return None

        # Sort by priority descending, then enqueue time ascending
        sorted_items = sorted(
            self._items.values(),
            key=lambda x: (-x.priority.value, x.enqueued_at),
        )

        best = sorted_items[0]
        req = self._requests.get(best.request_id)
        if req is None:
            self._items.pop(best.queue_id, None)
            return None

        # Mark as dispatched
        self._items[best.queue_id] = QueuedDispatch(
            queue_id=best.queue_id,
            request_id=best.request_id,
            priority=best.priority,
            enqueued_at=best.enqueued_at,
            status=DispatchStatus.dispatched(),
            retry_count=best.retry_count,
        )
        self._requests[best.request_id] = req.with_status(
            DispatchStatus.dispatched()
        )

        return (self._items[best.queue_id], req)

    def cancel(self, request_id: str) -> bool:
        """Cancel a queued dispatch by request_id."""
        for qid, item in list(self._items.items()):
            if item.request_id == request_id:
                self._items[qid] = QueuedDispatch(
                    queue_id=item.queue_id,
                    request_id=item.request_id,
                    priority=item.priority,
                    enqueued_at=item.enqueued_at,
                    status=DispatchStatus.cancelled(),
                    retry_count=item.retry_count,
                )
                req = self._requests.get(request_id)
                if req:
                    self._requests[request_id] = req.with_status(
                        DispatchStatus.cancelled()
                    )
                return True
        return False

    def reorder(self, request_id: str,
                new_priority: DispatchPriority) -> bool:
        """Change priority of a queued item."""
        for qid, item in list(self._items.items()):
            if item.request_id == request_id:
                self._items[qid] = QueuedDispatch(
                    queue_id=item.queue_id,
                    request_id=item.request_id,
                    priority=new_priority,
                    enqueued_at=item.enqueued_at,
                    status=item.status,
                    retry_count=item.retry_count,
                )
                return True
        return False

    def get(self, request_id: str) -> Optional[QueuedDispatch]:
        """Find queued dispatch by request_id."""
        for item in self._items.values():
            if item.request_id == request_id:
                return item
        return None

    def get_all(self) -> Tuple[QueuedDispatch, ...]:
        """Get all queued items, sorted by priority descending."""
        return tuple(
            sorted(self._items.values(),
                   key=lambda x: (-x.priority.value, x.enqueued_at))
        )

    def get_statistics(self) -> QueueStatistics:
        total = len(self._items)
        statuses = [i.status.value for i in self._items.values()]
        pending = statuses.count("pending") + statuses.count("queued")
        dispatched = statuses.count("dispatched")
        completed = statuses.count("completed")
        failed = statuses.count("failed")
        cancelled = statuses.count("cancelled")
        avg_prio = (
            sum(i.priority.value for i in self._items.values()) / total
            if total > 0 else 0.0
        )

        return QueueStatistics(
            total_queued=total,
            pending=pending,
            dispatched=dispatched,
            completed=completed,
            failed=failed,
            cancelled=cancelled,
            avg_priority=round(avg_prio, 2),
            estimated_wait_seconds=pending * 2,
        )

    def clear(self) -> None:
        self._items.clear()
        self._requests.clear()

    @property
    def count(self) -> int:
        return len(self._items)
