"""ConsoleRenderer — First implementation of RendererProtocol.

Renders ConsoleView, Dashboard, Widgets, Notifications, Timeline to stdout.
Uses RichAdapter — never imports Rich directly.
Pure presentation logic. No business logic. No domain access.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, List, Tuple
from datetime import datetime

from ..dashboard_model import MissionDashboardDTO
from ..action_center import ActionCenterDTO
from ..notification import Notification
from ..summary_builder import OperationalSummary
from .renderer import Renderer
from .console_view import ConsoleView, HeaderView, SidebarView, BodyView, StatusBarView, FooterView
from .dashboard_composer import ConsoleDashboard
from .widgets import WidgetRegistry, MissionWidgetCollection, ApprovalWidgetCollection
from .widgets import NotificationWidgetCollection, TimelineWidgetCollection, TrustWidget, HealthWidget
from .widgets import SummaryWidget, SchedulerWidget, WorkspaceWidget
from .navigation import NavigationState, SCREEN_LABELS
from .theme import Theme
from . import rich_adapter as rich


@dataclass
class ConsoleRenderer(Renderer):
    """Concrete Console Renderer — outputs to stdout via RichAdapter.

    Thread-safe: no mutable shared state. All rendering is stateless.
    Rich is optional: falls back to plain text if unavailable.
    """

    theme: Theme = field(default_factory=lambda: rich._STYLE_MAP and type("t", (), {"name": "dark"})())  # placeholder
    _console: Any = field(default_factory=rich.create_console)

    def __post_init__(self) -> None:
        from .theme import DarkTheme
        if not isinstance(self.theme, Theme):
            object.__setattr__(self, "theme", DarkTheme())

    # ── Public render methods ─────────────────────────────────────────

    def render_dashboard(self, dashboard: ConsoleDashboard) -> None:
        """Render full console dashboard."""
        output = self._build_dashboard_output(dashboard)
        self._print(output)

    def render_widget(self, widget_type: str, data: Any) -> None:
        """Render a single widget by type name."""
        output = self._render_widget_inner(widget_type, data)
        if output is not None:
            self._print(output)

    def render_notification(self, notification: Notification) -> None:
        """Render a single notification."""
        token = self._severity_token(notification.severity)
        line = f"[{notification.created_at[:19]}] {notification.title}"
        self._print(rich.styled_text(line, token))

    def render_summary(self, summary: OperationalSummary) -> None:
        """Render operational summary."""
        lines = [
            f"Mission: {summary.mission_name or summary.mission_id}",
            f"State:   {summary.mission_state}",
            "",
        ]
        if summary.problem:
            lines.append(f"Problem: {summary.problem}")
        if summary.decision_taken:
            lines.append(f"Decision: {summary.decision_taken}")
        if summary.evidence_items:
            lines.append("Evidence:")
            for item in summary.evidence_items[:8]:
                lines.append(f"  * {item}")
        lines.append(f"\nConfidence: {summary.decision_confidence:.1%}")
        lines.append(f"Risk:       {summary.decision_risk}")
        self._print("\n".join(lines))

    def render_timeline(self, events: Tuple[Any, ...]) -> None:
        """Render timeline events as a table."""
        if not events:
            self._print(rich.styled_text("No events in timeline.", "muted"))
            return

        table = rich.create_table("Timeline", box_style="simple")
        if table:
            rich.add_table_column(table, "Time", width=20)
            rich.add_table_column(table, "Type", width=16)
            rich.add_table_column(table, "Event")
            for ev in events:
                ts = getattr(ev, "timestamp", "") or getattr(ev, "created_at", "")[:19]
                etype = getattr(ev, "event_type", "") or getattr(ev, "type_id", "")
                title = getattr(ev, "title", str(ev))
                rich.add_table_row(table, ts, etype, title)
            self._print(table)
        else:
            # Plain fallback
            lines = ["Timeline:"]
            for ev in events:
                ts = getattr(ev, "timestamp", "") or getattr(ev, "created_at", "")[:19]
                title = getattr(ev, "title", str(ev))
                lines.append(f"  {ts}  {title}")
            self._print("\n".join(lines))

    def render_table(self, title: str, headers: Tuple[str, ...],
                     rows: Tuple[Tuple[str, ...], ...]) -> None:
        """Render a generic table."""
        if not headers:
            return
        table = rich.create_table(title, box_style="rounded")
        if table:
            for h in headers:
                rich.add_table_column(table, h)
            for row in rows:
                rich.add_table_row(table, *row)
            self._print(table)
        else:
            self._print(rich.plain_table(headers, rows))

    def render_mission(self, data: Any) -> None:
        """Render a single mission widget."""
        self._print(self._render_widget_inner("mission", data))

    # ── Full screen builder ───────────────────────────────────────────

    def render_console_view(self, view: ConsoleView,
                            nav: NavigationState,
                            registry: Optional[WidgetRegistry] = None) -> None:
        """Render full console screen from ViewModel + NavigationState.

        This is the main entry point for ConsoleSession.render().
        """
        lines: list[str] = []
        lines.append(self._build_header(view.header))
        lines.append(self._build_sidebar(view.sidebar, nav))
        lines.append(self._build_body(view.body, registry))
        lines.append(self._build_status_bar(view.status_bar))
        lines.append(self._build_footer(view.footer))

        output = "\n".join(lines)
        self._print(output)

    # ── Internal: dashboard output ────────────────────────────────────

    def _build_dashboard_output(self, d: ConsoleDashboard) -> str:
        lines: list[str] = []
        # Title
        lines.append(rich.separator(width=60))
        lines.append(f"  {d.title}")
        lines.append(rich.separator(width=60))

        # Mission stats
        lines.append(f"  Missions: {d.total_missions} total, "
                      f"{d.running_missions} running, "
                      f"{d.pending_missions} pending, "
                      f"{d.completed_missions} done, "
                      f"{d.failed_missions} failed")

        # Health
        h_token = "success" if d.health_status == "healthy" else "warning" if d.health_status == "degraded" else "error"
        lines.append(f"  Health:   {d.health_status} ({d.health_score:.1f}) "
                      f"[{d.health_warnings} warnings]")
        # Trust
        t_token = "success" if d.trust_grade in ("A", "A+") else "warning"
        lines.append(f"  Trust:    {d.trust_grade} ({d.trust_score:.2f}) "
                      f"[{d.total_decisions} decisions]")

        # Approvals
        a_token = "error" if d.pending_approvals > 5 else "warning" if d.pending_approvals > 0 else "success"
        lines.append(f"  Approvals: {d.pending_approvals} pending")

        # Notifications
        n_token = "error" if d.critical_notifications > 0 else "warning" if d.unread_notifications > 0 else "success"
        n_count = f"{d.unread_notifications} unread ({d.critical_notifications} critical)"
        lines.append(f"  Notifications: {n_count}")

        # Queue
        lines.append(f"  Queue:    {d.queue_size} items")
        if d.next_scheduled:
            lines.append(f"  Next:     {d.next_scheduled}")
        if d.latest_mission_summary:
            lines.append(f"  Latest:   {d.latest_mission_summary}")

        lines.append(rich.separator(width=60))
        lines.append(f"  Generated: {d.generated_at}")
        return "\n".join(lines)

    # ── Internal: section builders ────────────────────────────────────

    def _build_header(self, h: HeaderView) -> str:
        lines: list[str] = []
        lines.append(rich.separator(width=60))
        lines.append(f"  {h.title}")
        if h.subtitle:
            lines.append(f"  {h.subtitle}")
        status_tokens = {"healthy": "success", "running": "success",
                         "degraded": "warning", "unknown": "muted", "sleep": "info"}
        st = status_tokens.get(h.status, "muted")
        lines.append(f"  Status: {h.status}  |  Mode: {h.mode}")
        return "\n".join(lines)

    def _build_sidebar(self, s: SidebarView, nav: NavigationState) -> str:
        lines: list[str] = []
        lines.append("  Screens:")
        for section in nav.sections:
            for item in section.items:
                marker = ">" if item.screen == nav.active_screen else " "
                badge = f" [{item.notification_badge}]" if item.notification_badge else ""
                lines.append(f"    {marker} {item.shortcut}. {item.label}{badge}")
        if s.critical_alerts:
            lines.append(f"  ! {s.critical_alerts} critical alerts")
        if s.current_mission:
            lines.append(f"  Mission: {s.current_mission}")
        return "\n".join(lines)

    def _build_body(self, body: BodyView, registry: Optional[WidgetRegistry] = None) -> str:
        from .console_view import BodyView
        lines: list[str] = []
        lines.append(rich.separator(width=60))
        if body.title:
            lines.append(f"  {body.title}")
        if body.summary:
            lines.append(f"  {body.summary}")

        if registry:
            w_lines = self._render_registry(registry)
            if w_lines:
                lines.extend(w_lines)

        if body.items:
            lines.append("")
            for item in body.items:
                lines.append(f"  * {item}")
        if body.rows:
            lines.append("")
            lines.append(rich.plain_table(body.columns or (), body.rows))
        return "\n".join(lines)

    def _build_status_bar(self, sb: StatusBarView) -> str:
        parts = []
        if sb.mission_count:
            parts.append(f"M:{sb.mission_count}")
        if sb.pending_approvals:
            parts.append(f"A:{sb.pending_approvals}")
        if sb.trust_grade:
            parts.append(f"T:{sb.trust_grade}")
        if sb.health_status:
            parts.append(f"H:{sb.health_status}")
        if sb.last_event:
            parts.append(f"@{sb.last_event}")
        if sb.uptime:
            parts.append(sb.uptime)
        return "  " + " | ".join(parts) if parts else ""

    def _build_footer(self, f: FooterView) -> str:
        hints = " | ".join(f.hints[:6])
        sep_char = "-"
        return f"  {rich.separator(sep_char, 58)}\n  {hints}"

    # ── Internal: widget rendering ────────────────────────────────────

    def _render_widget_inner(self, widget_type: str, data: Any) -> Optional[str]:
        """Render a single widget by type. Returns text or None."""
        type_map = {
            "mission": self._render_mission_widget_h,
            "approval": self._render_approval_widget_h,
            "notification": self._render_notification_widget_h,
            "timeline": self._render_timeline_widget_h,
            "trust": self._render_trust_widget_h,
            "health": self._render_health_widget_h,
            "summary": self._render_summary_widget_h,
            "scheduler": self._render_scheduler_widget_h,
            "workspace": self._render_workspace_widget_h,
        }
        handler = type_map.get(widget_type)
        if handler:
            return handler(data)
        return None

    def _render_registry(self, r: WidgetRegistry) -> list[str]:
        lines: list[str] = []
        if r.health:
            lines.append(self._render_health_widget_h(r.health) or "")
        if r.mission:
            lines.append(self._mission_collection_text(r.mission))
        if r.approval:
            lines.append(self._approval_collection_text(r.approval))
        if r.notification:
            lines.append(self._notification_collection_text(r.notification))
        if r.timeline:
            lines.append(self._timeline_collection_text(r.timeline))
        if r.trust:
            lines.append(self._render_trust_widget_h(r.trust) or "")
        if r.scheduler:
            lines.append(self._render_scheduler_widget_h(r.scheduler) or "")
        if r.summary:
            lines.append(self._render_summary_widget_h(r.summary) or "")
        if r.workspace:
            lines.append(self._render_workspace_widget_h(r.workspace) or "")
        return [l for l in lines if l]

    def _mission_collection_text(self, mc: MissionWidgetCollection) -> str:
        lines = [f"  Missions ({mc.running} running, {mc.failed} failed, {mc.completed} done):"]
        for item in mc.items:
            lines.append(f"    * {item.mission_name} [{item.state}] "
                          f"{item.progress_pct:.0f}% " 
                          f"({item.steps_done}/{item.steps_total} steps)")
        return "\n".join(lines)

    def _approval_collection_text(self, ac: ApprovalWidgetCollection) -> str:
        if ac.total == 0:
            return "  No pending approvals."
        lines = [f"  Approvals ({ac.total} pending, {ac.urgent} urgent):"]
        for item in ac.items:
            r = "!" if item.risk == "high" else ""
            lines.append(f"    {r} {item.title} [{item.action}]")
        return "\n".join(lines)

    def _notification_collection_text(self, nc: NotificationWidgetCollection) -> str:
        if nc.total == 0:
            return "  No notifications."
        lines = [f"  Notifications ({nc.unread} unread, {nc.critical} critical):"]
        for item in nc.items:
            marker = "!" if item.severity == "critical" else "*"
            lines.append(f"    {marker} {item.title}")
        return "\n".join(lines)

    def _timeline_collection_text(self, tc: TimelineWidgetCollection) -> str:
        if tc.total == 0:
            return "  No timeline events."
        lines = [f"  Timeline ({tc.total} events):"]
        for item in tc.items:
            lines.append(f"    [{item.timestamp[:19]}] {item.title}")
        return "\n".join(lines)

    def _render_mission_widget_h(self, data: Any) -> Optional[str]:
        return None  # Will be used by collection viewer

    def _render_approval_widget_h(self, data: Any) -> Optional[str]:
        lines = [f"  Approval: {data.title}", f"    Action: {data.action}",
                  f"    Risk:   {data.risk}"]
        if data.reason:
            lines.append(f"    Reason: {data.reason}")
        return "\n".join(lines)

    def _render_notification_widget_h(self, data: Any) -> Optional[str]:
        return f"  [{data.type_id}] {data.title}"

    def _render_timeline_widget_h(self, data: Any) -> Optional[str]:
        return f"  [{data.timestamp[:19]}] {data.title}"

    def _render_trust_widget_h(self, data: TrustWidget) -> str:
        token = "success" if data.grade in ("A", "A+", "B+") else "warning"
        return f"  Trust: {data.grade} ({data.score:.2f}) — {data.total_decisions} decisions"

    def _render_health_widget_h(self, data: HealthWidget) -> str:
        token = "success" if data.status == "healthy" else "warning"
        s = f"  Health: {data.status} ({data.score:.1f})"
        if data.warnings:
            s += f" — {len(data.warnings)} warnings"
        return s

    def _render_summary_widget_h(self, data: SummaryWidget) -> str:
        lines = [f"  Summary: {data.title}"]
        if data.verdict:
            lines.append(f"  Verdict: {data.verdict}")
        if data.details:
            lines.append(f"  {data.details}")
        return "\n".join(lines)

    def _render_scheduler_widget_h(self, data: SchedulerWidget) -> str:
        s = f"  Queue: {data.queue_size} items"
        if data.running_count:
            s += f", {data.running_count} running"
        if data.next_scheduled:
            s += f", next: {data.next_scheduled}"
        return s

    def _render_workspace_widget_h(self, data: WorkspaceWidget) -> str:
        s = f"  Locks: {data.active_locks}/{data.total_locks} active"
        if data.lock_holders:
            s += f" — held by: {', '.join(data.lock_holders)}"
        return s

    # ── Helpers ───────────────────────────────────────────────────────

    def _severity_token(self, severity: str) -> str:
        mapping = {"critical": "error", "error": "error",
                    "warning": "warning", "attention": "warning",
                    "information": "info", "success": "success"}
        return mapping.get(severity, "info")

    def _print(self, output: Any) -> None:
        """Print output via Rich console or plain print."""
        if _has_console(self._console):
            self._console.print(output)
        else:
            print(output)


def _has_console(console: Any) -> bool:
    """Check whether console is a real Rich Console."""
    if not rich.has_rich():
        return False
    if console is None:
        return False
    try:
        from rich.console import Console as RConsole
        return isinstance(console, RConsole)
    except ImportError:
        return False
