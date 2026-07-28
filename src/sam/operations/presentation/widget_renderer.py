"""WidgetRenderer — Renders every widget type defined in Sprint 12.

All 18 widget renderers are pure functions or stateless methods.
No business logic. No domain imports. Uses RichAdapter for output.
"""

from __future__ import annotations
from typing import Any, Optional, List, Tuple
from dataclasses import dataclass, field

from .widgets import (
    MissionWidget, MissionWidgetCollection,
    ApprovalWidget, ApprovalWidgetCollection,
    NotificationWidget, NotificationWidgetCollection,
    TimelineEvent, TimelineWidgetCollection,
    TrustWidget, HealthWidget, WorkspaceWidget,
    SchedulerWidget, SummaryWidget,
)
from .theme import Theme
from . import rich_adapter as rich


@dataclass(frozen=True)
class WidgetRenderer:
    """Stateless renderer for all widget types.

    Each method accepts a widget dataclass and returns a string or Rich renderable.
    """

    theme: Theme = field(default_factory=lambda: None)  # type: ignore

    def render_widget(self, widget_type: str, data: Any) -> str:
        """Dispatch to the correct renderer by type name."""
        dispatch = {
            "mission": self._render_mission_item,
            "mission_collection": self._render_mission_collection,
            "approval": self._render_approval_item,
            "approval_collection": self._render_approval_collection,
            "notification": self._render_notification_item,
            "notification_collection": self._render_notification_collection,
            "timeline": self._render_timeline_item,
            "timeline_collection": self._render_timeline_collection,
            "trust": self._render_trust,
            "health": self._render_health,
            "workspace": self._render_workspace,
            "scheduler": self._render_scheduler,
            "summary": self._render_summary,
            "progress": self._render_progress,
            "status": self._render_status,
            "metric": self._render_metric,
            "alert": self._render_alert,
            "table": self._render_table_text,
            "list": self._render_list_text,
            "header": self._render_header_text,
            "footer": self._render_footer_text,
            "separator": self._render_separator,
            "action": self._render_action,
            "score": self._render_score,
        }
        handler = dispatch.get(widget_type)
        if handler:
            return handler(data)
        return f"[unknown widget: {widget_type}]"

    # ── Core Sprint 12 widgets ────────────────────────────────────────

    def _render_mission_item(self, w: MissionWidget) -> str:
        bar = self._progress_bar(w.progress_pct, 20)
        risk_m = "\u26a0" if w.risk == "high" else " "
        return (
            f"  {risk_m} {w.mission_name} [{w.state}]\n"
            f"    {bar} {w.progress_pct:.0f}%  "
            f"({w.steps_done}/{w.steps_total})"
        )

    def _render_mission_collection(self, mc: MissionWidgetCollection) -> str:
        if not mc.items:
            return "  No active missions."
        lines = [
            f"  Missions: {mc.running} running, {mc.failed} failed, {mc.completed} done"
        ]
        for item in mc.items:
            lines.append(self._render_mission_item(item))
        return "\n".join(lines)

    def _render_approval_item(self, w: ApprovalWidget) -> str:
        urgent = "\u26a0 " if w.risk == "high" else ""
        return f"  {urgent}[{w.approval_id[:8]}] {w.title} ({w.action})"

    def _render_approval_collection(self, ac: ApprovalWidgetCollection) -> str:
        if ac.total == 0:
            return "  No pending approvals."
        lines = [f"  Approvals: {ac.total} pending ({ac.urgent} urgent)"]
        for item in ac.items:
            lines.append(self._render_approval_item(item))
        return "\n".join(lines)

    def _render_notification_item(self, w: NotificationWidget) -> str:
        marker = "\u26a0" if w.severity == "critical" else "\u2022"
        return f"  {marker} [{w.type_id}] {w.title}"

    def _render_notification_collection(self, nc: NotificationWidgetCollection) -> str:
        if nc.total == 0:
            return "  No notifications."
        lines = [f"  Notifications: {nc.unread} unread, {nc.critical} critical"]
        for item in nc.items:
            lines.append(self._render_notification_item(item))
        return "\n".join(lines)

    def _render_timeline_item(self, ev: TimelineEvent) -> str:
        return f"  [{ev.timestamp[:19]}] {ev.title}"

    def _render_timeline_collection(self, tc: TimelineWidgetCollection) -> str:
        if tc.total == 0:
            return "  No timeline events."
        lines = [f"  Timeline ({tc.total} events):"]
        for item in tc.items:
            lines.append(self._render_timeline_item(item))
        return "\n".join(lines)

    def _render_trust(self, w: TrustWidget) -> str:
        t = "success" if w.grade in ("A", "A+", "B+") else "warning" if w.grade[0:1] == "B" else "error"
        styled = rich.styled_text(f"Trust: {w.grade} ({w.score:.2f})", t)
        return str(styled) if isinstance(styled, str) else f"Trust: {w.grade} ({w.score:.2f}) — {w.total_decisions} decisions"

    def _render_health(self, w: HealthWidget) -> str:
        t = "success" if w.status == "healthy" else "warning" if w.status == "degraded" else "error"
        s = f"Health: {w.status} ({w.score:.1f})"
        if w.warnings:
            s += f" — {len(w.warnings)} warnings"
        return s

    def _render_workspace(self, w: WorkspaceWidget) -> str:
        s = f"Locks: {w.active_locks}/{w.total_locks} active"
        if w.lock_holders:
            s += f" — held by: {', '.join(w.lock_holders)}"
        return s

    def _render_scheduler(self, w: SchedulerWidget) -> str:
        s = f"Queue: {w.queue_size} items"
        if w.running_count:
            s += f", {w.running_count} running"
        if w.next_scheduled:
            s += f", next: {w.next_scheduled}"
        return s

    def _render_summary(self, w: SummaryWidget) -> str:
        lines = [f"Summary: {w.title}"]
        if w.verdict:
            lines.append(f"  Verdict: {w.verdict}")
        if w.details:
            lines.append(f"  {w.details}")
        if w.trust_grade:
            lines.append(f"  Trust: {w.trust_grade}")
        if w.duration:
            lines.append(f"  Duration: {w.duration}")
        if w.steps:
            lines.append(f"  Steps: {w.steps}")
        return "\n".join(lines)

    # ── Extended widget types ─────────────────────────────────────────

    def _render_progress(self, data: Any) -> str:
        """Render a progress bar from a dict or object with value/max/title."""
        title = self._get_attr(data, "title", "")
        value = float(self._get_attr(data, "value", 0))
        maximum = float(self._get_attr(data, "max", 100))
        pct = (value / maximum * 100) if maximum > 0 else 0
        bar = self._progress_bar(pct, 20)
        return f"  {title}: {bar} {pct:.0f}%" if title else f"  {bar} {pct:.0f}%"

    def _render_status(self, data: Any) -> str:
        """Render a status indicator."""
        label = self._get_attr(data, "label", "Status")
        state = self._get_attr(data, "state", "unknown")
        icon = {"healthy": "\u2714", "running": "\u25b6", "degraded": "\u26a0",
                 "failed": "\u2718", "sleep": "\u23f3", "unknown": "?"}.get(state, "?")
        return f"  {label}: {icon} {state}"

    def _render_metric(self, data: Any) -> str:
        """Render a metric value with optional delta."""
        name = self._get_attr(data, "name", "Metric")
        value = self._get_attr(data, "value", "—")
        unit = self._get_attr(data, "unit", "")
        delta = self._get_attr(data, "delta", None)
        s = f"  {name}: {value}{unit}"
        if delta is not None:
            sign = "+" if float(delta) > 0 else ""
            s += f" ({sign}{delta})"
        return s

    def _render_alert(self, data: Any) -> str:
        """Render an alert message."""
        severity = self._get_attr(data, "severity", "info")
        message = self._get_attr(data, "message", str(data))
        icon = {"critical": "\U0001f6a8", "error": "\u2716", "warning": "\u26a0",
                 "info": "\u2139", "success": "\u2714"}.get(severity, "\u2139")
        return f"  {icon} {message}"

    def _render_table_text(self, data: Any) -> str:
        """Render a plain text table from dict/object with headers/rows."""
        headers = tuple(self._get_attr(data, "headers", ()))
        rows = tuple(self._get_attr(data, "rows", ()))
        if not headers:
            return "  [empty table]"
        return "  " + rich.plain_table(headers, rows).replace("\n", "\n  ")

    def _render_list_text(self, data: Any) -> str:
        """Render a bulleted list."""
        items = self._get_attr(data, "items", [])
        if isinstance(data, (list, tuple)):
            items = data
        if not items:
            return "  [empty list]"
        return "\n".join(f"  \u2022 {item}" for item in items)

    def _render_header_text(self, data: Any) -> str:
        """Render a section header."""
        title = self._get_attr(data, "title", str(data))
        width = int(self._get_attr(data, "width", 60))
        return f"\n  {title}\n  {rich.separator(width=width)}"

    def _render_footer_text(self, data: Any) -> str:
        """Render a footer line."""
        text = self._get_attr(data, "text", str(data))
        return f"  {text}"

    def _render_separator(self, data: Any) -> str:
        """Render a separator line."""
        char = self._get_attr(data, "char", "\u2500")
        width = int(self._get_attr(data, "width", 60))
        return f"  {rich.separator(char, width)}"

    def _render_action(self, data: Any) -> str:
        """Render an actionable item."""
        action = self._get_attr(data, "action", "?")
        description = self._get_attr(data, "description", str(data))
        shortcut = self._get_attr(data, "shortcut", "")
        sh = f"[{shortcut}] " if shortcut else ""
        return f"  {sh}{action}: {description}"

    def _render_score(self, data: Any) -> str:
        """Render a score with visual indicator."""
        label = self._get_attr(data, "label", "Score")
        score = float(self._get_attr(data, "score", 0))
        maximum = float(self._get_attr(data, "max", 100))
        pct = (score / maximum * 100) if maximum > 0 else 0
        bar = self._progress_bar(pct, 15)
        return f"  {label}: {bar} {score:.1f}/{maximum:.0f}"

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _progress_bar(pct: float, width: int = 20) -> str:
        """Draw a simple progress bar string."""
        filled = int(pct / 100 * width)
        filled = max(0, min(width, filled))
        empty = width - filled
        block = "#"
        return f"[{block * filled}{' ' * empty}]"

    @staticmethod
    def _get_attr(obj: Any, name: str, default: Any = "") -> Any:
        """Safely get an attribute from any object type."""
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)
