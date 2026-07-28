"""NotificationWorkspace — Notification workspace for the SAM Console.

Support: unread, read, dismiss, filter priority, clear expired,
notification history. Uses existing Notification DTO from Sprint 11.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple
from datetime import datetime

from ...notification import Notification


@dataclass
class NotificationItem:
    """A notification in the workspace (wraps existing Notification DTO)."""
    notification: Notification
    read: bool = False
    dismissed: bool = False


@dataclass
class NotificationWorkspace:
    """Notification workspace.

    Manages notifications from the DTO layer.
    Does not store state on behalf of the notification system.

    Usage:
        workspace = NotificationWorkspace()
        workspace.add(notification_critical_alert(...))
        workspace.add(notification_mission_started(...))
        workspace.mark_read(n_id)
        workspace.dismiss(n_id)
        workspace.clear_expired()
    """

    _items: List[NotificationItem] = field(default_factory=list)
    _dismiss_callbacks: List[Callable[[str], None]] = field(default_factory=list)

    # ── Adding ───────────────────────────────────────────────────────

    def add(self, notification: Notification) -> None:
        """Add a notification to the workspace."""
        self._items.append(NotificationItem(
            notification=notification,
        ))

    def add_many(self, notifications: Tuple[Notification, ...]) -> None:
        """Add multiple notifications at once."""
        for n in notifications:
            self._items.append(NotificationItem(notification=n))

    # ── Read/unread ─────────────────────────────────────────────────

    def mark_read(self, item_id: str) -> bool:
        """Mark a notification as read by ID."""
        for item in self._items:
            if item.notification.source_id == item_id and not item.read:
                item.read = True
                return True
        return False

    def mark_all_read(self) -> None:
        for item in self._items:
            if not item.read:
                item.read = True

    # ── Dismiss ──────────────────────────────────────────────────────

    def dismiss(self, item_id: str) -> bool:
        """Dismiss a notification by ID."""
        for item in self._items:
            if item.notification.source_id == item_id and not item.dismissed:
                item.dismissed = True
                for cb in self._dismiss_callbacks:
                    try:
                        cb(item_id)
                    except Exception:
                        pass
                return True
        return False

    def dismiss_all(self) -> None:
        for item in self._items:
            if not item.dismissed:
                item.dismissed = True

    def on_dismiss(self, callback: Callable[[str], None]) -> None:
        """Register dismiss callback."""
        self._dismiss_callbacks.append(callback)

    # ── Filtering ────────────────────────────────────────────────────

    @property
    def unread(self) -> Tuple[NotificationItem, ...]:
        return tuple(
            i for i in self._items
            if not i.read and not i.dismissed
        )

    @property
    def read(self) -> Tuple[NotificationItem, ...]:
        return tuple(
            i for i in self._items
            if i.read and not i.dismissed
        )

    @property
    def dismissed(self) -> Tuple[NotificationItem, ...]:
        return tuple(i for i in self._items if i.dismissed)

    @property
    def all_active(self) -> Tuple[NotificationItem, ...]:
        return tuple(i for i in self._items if not i.dismissed)

    def filter_priority(self, priority: str) -> Tuple[NotificationItem, ...]:
        """Filter by type/severity keyword."""
        p = priority.lower()
        return tuple(
            i for i in self._items if not i.dismissed
            and (p in i.notification.type_id.lower()
                 or p in i.notification.title.lower())
        )

    def filter_by_type(self, type_id: str) -> Tuple[NotificationItem, ...]:
        return tuple(
            i for i in self._items if not i.dismissed
            and i.notification.type_id == type_id
        )

    # ── Counts ───────────────────────────────────────────────────────

    @property
    def unread_count(self) -> int:
        return len(self.unread)

    @property
    def total_active(self) -> int:
        return len(self.all_active)

    @property
    def badge_count(self) -> int:
        return self.unread_count

    # ── Expiry ───────────────────────────────────────────────────────

    def clear_expired(self, max_age_seconds: int = 86400) -> int:
        """Dismiss notifications older than max_age_seconds. Returns count."""
        now = datetime.now()
        expired: List[str] = []
        for item in self._items:
            if item.dismissed:
                continue
            try:
                created = datetime.fromisoformat(
                    item.notification.created_at
                )
                if (now - created).total_seconds() > max_age_seconds:
                    expired.append(item.notification.source_id)
            except (ValueError, TypeError):
                continue

        for eid in expired:
            self.dismiss(eid)
        return len(expired)

    # ── History ──────────────────────────────────────────────────────

    @property
    def history(self) -> Tuple[NotificationItem, ...]:
        """All notifications including dismissed, newest first."""
        return tuple(reversed(self._items))

    def clear_history(self) -> None:
        """Remove all notification items from workspace."""
        self._items.clear()

    # ── Diagnostic ───────────────────────────────────────────────────

    def summary(self) -> dict:
        return {
            "total": len(self._items),
            "unread": self.unread_count,
            "active": self.total_active,
            "dismissed": len(self.dismissed),
        }
