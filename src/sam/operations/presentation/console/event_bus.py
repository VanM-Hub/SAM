"""EventBus — Pub/sub event bus for Console events.

All console events flow through this bus.
Renderers don't know each other — they subscribe to events.
No threading: synchronous dispatch (no deadlock risk in single-thread).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime


# ── Event types ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class ScreenChanged:
    """Emitted when the active screen changes."""
    screen: str
    previous: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class CommandExecuted:
    """Emitted when a command is executed."""
    command: str
    success: bool
    message: str = ""
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class RefreshRequested:
    """Emitted when a refresh is requested."""
    mode: str = "full"
    source: str = "manual"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class MissionSelected:
    """Emitted when a mission is selected or focused."""
    mission_id: str
    mission_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class NotificationRaised:
    """Emitted when a notification is raised."""
    notification_id: str
    title: str
    severity: str = "information"
    count: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class ThemeChanged:
    """Emitted when the console theme is switched."""
    new_theme: str
    old_theme: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class ErrorOccurred:
    """Emitted when a runtime error occurs."""
    source: str
    message: str
    recoverable: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class ShutdownRequested:
    """Emitted when shutdown is requested."""
    reason: str = "user_request"
    graceful: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


EVENT_TYPES = (
    ScreenChanged, CommandExecuted, RefreshRequested,
    MissionSelected, NotificationRaised, ThemeChanged,
    ErrorOccurred, ShutdownRequested,
)


class EventBus:
    """Simple pub/sub event bus.

    Synchronous dispatch only — no threading, no async.
    Subscribers are called in registration order.
    No deadlock risk: events are dispatched immediately, not queued.

    Usage:
        bus = EventBus()
        bus.subscribe(ScreenChanged, handler)
        bus.publish(ScreenChanged(screen="missions", previous="dashboard"))
    """

    def __init__(self) -> None:
        self._subscribers: Dict[type, List[Callable]] = {}
        self._history: List[Any] = []

    # ── Subscription ──────────────────────────────────────────────────

    def subscribe(self, event_type: type, handler: Callable) -> None:
        """Subscribe a handler to an event type.

        handler receives one argument: the event instance.
        """
        if not isinstance(event_type, type):
            raise TypeError(f"event_type must be a class, got {type(event_type)}")
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: type, handler: Callable) -> bool:
        """Remove a handler subscription. Returns True if found and removed."""
        handlers = self._subscribers.get(event_type)
        if not handlers:
            return False
        try:
            handlers.remove(handler)
            return True
        except ValueError:
            return False

    def clear_all(self) -> None:
        """Remove all subscriptions."""
        self._subscribers.clear()

    # ── Publishing ────────────────────────────────────────────────────

    def publish(self, event: Any) -> None:
        """Publish an event to all subscribers.

        Events are dispatched synchronously.
        Subscriber exceptions are caught and logged (no crash cascade).
        """
        self._history.append(event)

        handlers = self._subscribers.get(type(event), [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Suppress subscriber errors to prevent cascade
                pass

    # ── Queries ───────────────────────────────────────────────────────

    @property
    def event_count(self) -> int:
        return len(self._history)

    @property
    def subscriber_count(self) -> int:
        return sum(len(h) for h in self._subscribers.values())

    def recent_events(self, n: int = 10) -> Tuple[Any, ...]:
        """Get the last N events published."""
        return tuple(self._history[-n:])

    def events_by_type(self, event_type: type) -> Tuple[Any, ...]:
        """Get all events of a specific type."""
        return tuple(e for e in self._history if isinstance(e, event_type))

    def clear_history(self) -> None:
        """Clear event history without affecting subscriptions."""
        self._history.clear()

    # ── Diagnostic ────────────────────────────────────────────────────

    def subscriber_summary(self) -> Dict[str, int]:
        """Return {event_type_name: subscriber_count} for all types."""
        result: dict = {}
        for event_type, handlers in self._subscribers.items():
            result[event_type.__name__] = len(handlers)
        return result
