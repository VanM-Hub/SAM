"""DesktopRendererAdapter — Bridge between RendererProtocol and Desktop Qt widgets.

Implements RendererProtocol (Sprint 12) for the Desktop host.
Translates render calls into WidgetActions that Qt widgets will consume.

This is a BRIDGE — no widget implementations.
Widget shapes (QVBoxLayout, QTreeWidget, etc.) belong in Sprint 17+.

No business logic. No domain access. Pure adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union
from datetime import datetime

from ..renderer import Renderer
from ...summary_builder import OperationalSummary


# ── Widget Actions ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class WidgetAction:
    """An action that a Qt widget should perform.

    These are the ONLY commands Desktop sends to Qt widgets.
    No raw render data. No domain objects.
    """
    action: str  # "set_content", "append", "clear", "update", "show", "hide"
    widget_id: str
    data: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def set_content(widget_id: str, content: str, **meta: str) -> WidgetAction:
        return WidgetAction(
            action="set_content",
            widget_id=widget_id,
            data=content,
            metadata=meta,
        )

    @staticmethod
    def append(widget_id: str, content: str, **meta: str) -> WidgetAction:
        return WidgetAction(
            action="append",
            widget_id=widget_id,
            data=content,
            metadata=meta,
        )

    @staticmethod
    def clear(widget_id: str) -> WidgetAction:
        return WidgetAction(
            action="clear",
            widget_id=widget_id,
        )

    @staticmethod
    def update(widget_id: str, data: str, **meta: str) -> WidgetAction:
        return WidgetAction(
            action="update",
            widget_id=widget_id,
            data=data,
            metadata=meta,
        )

    @staticmethod
    def show(widget_id: str) -> WidgetAction:
        return WidgetAction(
            action="show",
            widget_id=widget_id,
        )

    @staticmethod
    def hide(widget_id: str) -> WidgetAction:
        return WidgetAction(
            action="hide",
            widget_id=widget_id,
        )


# ── Desktop Widget Regions ────────────────────────────────────────────

class WidgetRegion:
    """Identifiers for desktop widget regions.

    Desktop widgets are identified by region + view type.
    These constants are used by renderer_adapter to route render
    calls to the correct widget.
    """
    DASHBOARD = "dashboard"
    MISSION_LIST = "mission_list"
    MISSION_DETAIL = "mission_detail"
    TIMELINE = "timeline"
    APPROVAL_LIST = "approval_list"
    APPROVAL_DETAIL = "approval_detail"
    NOTIFICATION_LIST = "notification_list"
    LOG_VIEW = "log_view"
    STATUS_BAR = "status_bar"
    NAV_PANEL = "nav_panel"
    RIGHT_PANEL = "right_panel"
    SUMMARY = "summary"

    WIDGET_IDS = [
        DASHBOARD, MISSION_LIST, MISSION_DETAIL, TIMELINE,
        APPROVAL_LIST, APPROVAL_DETAIL, NOTIFICATION_LIST,
        LOG_VIEW, STATUS_BAR, NAV_PANEL, RIGHT_PANEL, SUMMARY,
    ]


# ── Action Queue ──────────────────────────────────────────────────────

@dataclass
class ActionQueue:
    """Queues WidgetActions for batched processing.

    Desktop widgets process actions in batches.
    This avoids tight coupling between render calls and UI updates.
    """

    _actions: List[WidgetAction] = field(default_factory=list)

    def enqueue(self, action: WidgetAction) -> None:
        """Add an action to the queue."""
        self._actions.append(action)

    def dequeue_all(self) -> Tuple[WidgetAction, ...]:
        """Get and clear all pending actions."""
        actions = tuple(self._actions)
        self._actions.clear()
        return actions

    def dequeue(self) -> Optional[WidgetAction]:
        """Get the next pending action."""
        if not self._actions:
            return None
        return self._actions.pop(0)

    @property
    def pending_count(self) -> int:
        return len(self._actions)

    @property
    def has_pending(self) -> bool:
        return len(self._actions) > 0

    def clear(self) -> None:
        self._actions.clear()


# ── Desktop Renderer Adapter ──────────────────────────────────────────

@dataclass
class DesktopRendererAdapter:
    """Implements RendererProtocol for Desktop host.

    Translates render_* calls into WidgetActions.
    Qt widgets read actions from the queue.

    This is a BRIDGE — no Qt references.
    Widget implementation belongs in Sprint 17+.
    """

    action_queue: ActionQueue = field(default_factory=ActionQueue)
    _render_count: int = 0

    # ── Renderer Protocol implementation ─────────────────────────────

    def render_dashboard(self, view: object) -> None:
        """Render a dashboard view.

        Translates view data into a WidgetAction for the dashboard region.
        view: ConsoleDashboard (from Sprint 12)
        """
        self._render_count += 1

        # Extract dashboard data (safe getattr)
        summary = self._safe_str(view, 'summary_line', '')
        missions = self._safe_str(view, 'mission_summary', '')
        health = getattr(view, 'health_status', 'unknown')
        trust = getattr(view, 'trust_grade', '?')

        content = (
            f"Dashboard | Missions: {missions} | Health: {health} | "
            f"Trust: {trust} | {summary}"
        )
        self.action_queue.enqueue(
            WidgetAction.set_content(
                WidgetRegion.DASHBOARD,
                content,
                type="dashboard",
            )
        )

    def render_widget(self, widget_type: str, data: object) -> None:
        """Render a single widget.

        Translates widget data into a WidgetAction.
        widget_type: widget identifier from Sprint 12 WidgetRegistry
        data: widget payload
        """
        self._render_count += 1
        content = self._safe_str(data, 'summary', str(data) if data else '')

        self.action_queue.enqueue(
            WidgetAction.set_content(
                widget_type,
                content,
                type="widget",
            )
        )

    def render_notification(self, notification: object) -> None:
        """Render a notification.

        Translates notification data into a WidgetAction.
        notification: Notification DTO from Sprint 11
        """
        self._render_count += 1
        title = self._safe_str(notification, 'title', 'Notification')
        message = self._safe_str(notification, 'message', '')
        source = self._safe_str(notification, 'source_id', '')

        content = f"[{title}] {message}"
        if source:
            content = f"[{title} - {source}] {message}"

        self.action_queue.enqueue(
            WidgetAction.append(
                WidgetRegion.NOTIFICATION_LIST,
                content,
                type="notification",
            )
        )

    def render_summary(self, summary: OperationalSummary) -> None:
        """Render an operational summary.

        Translates summary data into a WidgetAction.
        summary: OperationalSummary from Sprint 4
        """
        self._render_count += 1
        content = self._safe_str(summary, 'summary', str(summary) if summary else '')

        self.action_queue.enqueue(
            WidgetAction.set_content(
                WidgetRegion.SUMMARY,
                content,
                type="summary",
            )
        )

    def render_timeline(self, events: tuple) -> None:
        """Render timeline events.

        Translates event data into a WidgetAction.
        events: tuple of event dicts or Event objects
        """
        self._render_count += 1
        lines = []
        for ev in events[:100]:  # limit to 100 events
            ts = self._safe_str(ev, 'timestamp', '')
            title = self._safe_str(ev, 'title', '')
            severity = ''
            if hasattr(ev, 'severity'):
                severity = getattr(ev, 'severity', '')
            elif isinstance(ev, dict):
                severity = ev.get('severity', '')

            prefix = f"[{severity}]" if severity else ""
            if ts:
                lines.append(f"{ts} {prefix} {title}")
            else:
                lines.append(f"{prefix} {title}")

        content = "\n".join(lines) if lines else "No events"

        self.action_queue.enqueue(
            WidgetAction.set_content(
                WidgetRegion.TIMELINE,
                content,
                type="timeline",
            )
        )

    # ── Status bar integration ────────────────────────────────────────

    def update_status_bar(self, text: str) -> None:
        """Update the status bar text."""
        self.action_queue.enqueue(
            WidgetAction.set_content(
                WidgetRegion.STATUS_BAR,
                text,
                type="status",
            )
        )

    def update_nav_panel(self, nav_text: str) -> None:
        """Update the navigation panel."""
        self.action_queue.enqueue(
            WidgetAction.set_content(
                WidgetRegion.NAV_PANEL,
                nav_text,
                type="navigation",
            )
        )

    # ── Batch processing ──────────────────────────────────────────────

    def flush(self) -> Tuple[WidgetAction, ...]:
        """Get all pending actions and clear the queue."""
        return self.action_queue.dequeue_all()

    @property
    def render_count(self) -> int:
        return self._render_count

    # ── Diagnostics ───────────────────────────────────────────────────

    def summary(self) -> str:
        return (
            f"DesktopRendererAdapter: {self._render_count} renders, "
            f"{self.action_queue.pending_count} pending actions"
        )

    # ── Internal helpers ──────────────────────────────────────────────

    @staticmethod
    def _safe_str(obj: object, attr: str, default: str = '') -> str:
        """Safely extract a string attribute from any object."""
        if obj is None:
            return default
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            if val is None:
                return default
            return str(val)
        if isinstance(obj, dict):
            val = obj.get(attr, default)
            if val is None:
                return default
            return str(val)
        return default
