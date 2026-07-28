"""NotificationCenter — Runtime notification management for Console.

Uses DTO from operations/notification.py (Sprint 11) without modification.
Adds: queue, priority, expire, dismiss, unread, badge count.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Optional, Tuple
from datetime import datetime, timedelta
import time
import threading

from ...notification import (
    Notification, NotificationStore,
    NOTIFICATION_TYPES, NOTIFICATION_SEVERITY,
    CRITICAL_ALERT,
)


@dataclass(frozen=True)
class NotificationItem:
    """A notification with runtime tracking info (immutable wrapper).

    Wraps the DTO Notification with runtime state.
    Does NOT modify the DTO.
    """
    notification: Notification
    item_id: str = ""
    raised_at: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 0  # Higher = more urgent
    expires_at: Optional[str] = None
    badge_count: int = 1

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expiry
        except (ValueError, TypeError):
            return False

    @property
    def is_critical(self) -> bool:
        return self.notification.is_critical

    @property
    def severity(self) -> str:
        return self.notification.severity


# Priority levels (higher = more urgent)
PRIORITY_CRITICAL = 100
PRIORITY_ERROR = 50
PRIORITY_WARNING = 20
PRIORITY_NORMAL = 0

_SEVERITY_PRIORITY = {
    "critical": PRIORITY_CRITICAL,
    "error": PRIORITY_ERROR,
    "warning": PRIORITY_WARNING,
    "attention": PRIORITY_WARNING,
    "information": PRIORITY_NORMAL,
}


class NotificationCenter:
    """Runtime notification center.

    Manages notification queue with priority, expiry, and badge counting.
    Uses Notification (Sprint 11 DTO) without modification.
    Thread-safe: uses a lock for concurrent access.

    Usage:
        center = NotificationCenter()
        center.push(Notification(...))
        count = center.unread_count
        center.dismiss("notif_1")
    """

    def __init__(self, max_size: int = 200,
                 default_expiry_seconds: Optional[int] = 3600) -> None:
        self._items: List[NotificationItem] = []
        self._max_size = max_size
        self._default_expiry_seconds = default_expiry_seconds
        self._lock = threading.Lock()
        self._store = NotificationStore(max_size=max_size)

    # ── Push / Add ────────────────────────────────────────────────────

    def push(self, notification: Notification,
             item_id: Optional[str] = None,
             priority: Optional[int] = None,
             expire_seconds: Optional[int] = None) -> NotificationItem:
        """Add a notification to the queue.

        Args:
            notification: Notification DTO (Sprint 11).
            item_id: Optional ID for tracking/dismissal. Auto-generated if empty.
            priority: Priority override. Auto-calculated from severity if None.
            expire_seconds: Seconds until expiry. Uses default if None.

        Returns the NotificationItem added.
        """
        actual_id = item_id or f"notif_{int(time.time() * 1000)}_{len(self._items)}"
        actual_priority = (
            priority if priority is not None
            else _SEVERITY_PRIORITY.get(notification.severity, PRIORITY_NORMAL)
        )
        expire_dt: Optional[str] = None
        expiry = expire_seconds if expire_seconds is not None else self._default_expiry_seconds
        if expiry is not None:
            expire_dt = (datetime.now() + timedelta(seconds=expiry)).isoformat()

        item = NotificationItem(
            notification=notification,
            item_id=actual_id,
            priority=actual_priority,
            expires_at=expire_dt,
        )

        with self._lock:
            self._items.append(item)
            self._store.push(notification)
            # Sort by priority (highest first), then by time (newest first)
            self._items.sort(key=lambda x: (-x.priority, x.raised_at), reverse=False)
            # Trim to max_size
            while len(self._items) > self._max_size:
                self._items.pop(0)

        return item

    # ── Queries ───────────────────────────────────────────────────────

    @property
    def unread_count(self) -> int:
        """Number of non-acknowledged notifications."""
        with self._lock:
            return sum(
                1 for item in self._items
                if not item.notification.acknowledged and not item.is_expired
            )

    @property
    def critical_count(self) -> int:
        """Number of critical notifications."""
        with self._lock:
            return sum(
                1 for item in self._items
                if item.is_critical
                and not item.notification.acknowledged
                and not item.is_expired
            )

    @property
    def badge_count(self) -> int:
        """Total badge count (unread + critical weighted)."""
        unread = self.unread_count
        critical = self.critical_count * 2  # Critical counts double
        return unread + critical

    def all(self, include_expired: bool = False) -> Tuple[NotificationItem, ...]:
        """Get all notifications, sorted by priority.
        
        Args:
            include_expired: If True, includes expired notifications.
        """
        with self._lock:
            items = list(self._items)
        if not include_expired:
            items = [i for i in items if not i.is_expired]
        return tuple(items)

    def unread(self) -> Tuple[NotificationItem, ...]:
        """Get all unread notifications, sorted by priority."""
        with self._lock:
            return tuple(
                item for item in self._items
                if not item.notification.acknowledged and not item.is_expired
            )

    def critical(self) -> Tuple[NotificationItem, ...]:
        """Get all critical notifications."""
        with self._lock:
            return tuple(
                item for item in self._items
                if item.is_critical and not item.is_expired
            )

    def get_by_id(self, item_id: str) -> Optional[NotificationItem]:
        """Get a notification by item_id."""
        with self._lock:
            for item in self._items:
                if item.item_id == item_id:
                    return item
        return None

    # ── Dismissal ─────────────────────────────────────────────────────

    def dismiss(self, item_id: str) -> bool:
        """Acknowledge/dismiss a notification by item_id.

        Returns True if found and dismissed.
        """
        with self._lock:
            for item in self._items:
                if item.item_id == item_id:
                    item.notification.acknowledged = True
                    return True
        return False

    def dismiss_all(self) -> int:
        """Acknowledge all notifications.

        Returns count of dismissed items.
        """
        count = 0
        with self._lock:
            for item in self._items:
                if not item.notification.acknowledged:
                    item.notification.acknowledged = True
                    count += 1
        return count

    def dismiss_by_source(self, source_id: str) -> int:
        """Acknowledge all notifications from a specific source.

        Returns count of dismissed items.
        """
        count = 0
        with self._lock:
            for item in self._items:
                if (item.notification.source_id == source_id
                        and not item.notification.acknowledged):
                    item.notification.acknowledged = True
                    count += 1
        return count

    # ── Maintenance ───────────────────────────────────────────────────

    def purge_expired(self) -> int:
        """Remove all expired notifications from the queue.

        Returns count of purged items.
        """
        count = 0
        with self._lock:
            remaining: list = []
            for item in self._items:
                if item.is_expired:
                    count += 1
                else:
                    remaining.append(item)
            self._items = remaining
        return count

    def clear(self) -> None:
        """Remove all notifications."""
        with self._lock:
            self._items.clear()
            self._store = NotificationStore(max_size=self._max_size)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[NotificationItem]:
        return iter(self.all())
