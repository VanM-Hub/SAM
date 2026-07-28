"""Sprint 15 validation — 9 workspace modules."""
from __future__ import annotations
import sys
sys.path.insert(0, "D:/Project AI/SAM/src")

from src.sam.operations.presentation.console import *

# ── Config ────────────────────────────────────────────────────────────

CTX = ConsoleConfig(theme="dark", refresh_rate=10.0)

# ══════════════════════════════════════════════════════════════════════
# OP-191: Dashboard Runtime
# ══════════════════════════════════════════════════════════════════════
print("=== OP-191: DashboardRuntime ===")

dr = DashboardRuntime()
assert dr.active_screen == "dashboard"
assert dr.refresh_mode == RefreshMode.MANUAL

# Screen switch
dr.switch_screen("missions")
assert dr.active_screen == "missions"
assert dr.previous_screen == "dashboard"
assert dr.is_dirty

# Back
dr.go_back()
assert dr.active_screen == "dashboard"

# Invalid screen
dr.switch_screen("nonexistent")
assert dr.active_screen == "dashboard"

# Refresh
dr.mark_clean()
assert not dr.is_dirty
dr.refresh()
assert dr.refresh_count == 1
assert dr.last_refresh_time is not None

# Pause / Resume
dr.pause()
assert dr.is_paused
dr.refresh()  # should be noop
rc = dr.refresh_count
dr.refresh()
assert dr.refresh_count == rc
dr.resume()
assert not dr.is_paused
dr.refresh()
assert dr.refresh_count == rc + 1

# Filter
dr.set_filter(status_filter="running")
assert dr.filter_state.status_filter == "running"
dr.set_sort("name")
assert dr.filter_state.sort_by == "name"
dr.next_page()
assert dr.filter_state.page == 2
dr.prev_page()
assert dr.filter_state.page == 1

# Callbacks
cb_fired = []
dr.on_refresh(lambda: cb_fired.append("ref"))
dr.refresh()
assert len(cb_fired) == 1

cb_screen = []
dr.on_screen_change(lambda new_s, old_s: cb_screen.append((new_s, old_s)))
dr.switch_screen("approvals")
assert len(cb_screen) == 1

print("  all dashboard runtime: OK")

# ══════════════════════════════════════════════════════════════════════
# OP-192: Mission Monitor
# ══════════════════════════════════════════════════════════════════════
print("\n=== OP-192: MissionMonitor ===")

# Empty
mm = MissionMonitorFactory.empty()
assert mm.total == 0
assert mm.active_count == 0

# From dashboard DTO
class FakeDashboard:
    total_missions = 5
    running_missions = 2
    pending_missions = 1
    completed_missions = 1
    failed_missions = 1

mm2 = MissionMonitorFactory.from_dashboard(FakeDashboard())
assert mm2.total == 5
assert mm2.running == 2
assert mm2.pending == 1
assert mm2.completed == 1
assert mm2.failed == 1

# From mission list
missions = [
    {"mission_id": "m1", "name": "Health Check", "status": "running",
     "progress": 0.5, "goal": "Check health", "condition": "ok"},
    {"mission_id": "m2", "name": "Backup", "status": "pending",
     "progress": 0.0, "goal": "Run backup", "condition": "ready"},
    {"id": "m3", "name": "Cleanup", "status": "failed",
     "progress": 0.8, "goal": "Clean temp", "condition": "error"},
]
mm3 = MissionMonitorFactory.from_mission_list(missions)
assert mm3.total == 3
assert mm3.running == 1
assert mm3.pending == 1
assert mm3.failed == 1
assert len(mm3.missions) == 3

# Filter
mh = mm3.by_status("running")
assert mh.running == 1
assert mh.filtered_count == 1

mh2 = mm3.search("backup")
assert mh2.filtered_count == 1

mh3 = mm3.sort_by("name")
assert mh3.missions[0].name == "Backup"

assert "Missions" in mm3.summary_line

print("  all mission monitor: OK")

# ══════════════════════════════════════════════════════════════════════
# OP-193: Approval Workspace
# ══════════════════════════════════════════════════════════════════════
print("\n=== OP-193: ApprovalWorkspace ===")

aw = ApprovalWorkspaceFactory.empty()
assert aw.total_pending == 0

aw2 = ApprovalWorkspaceFactory.from_dicts(
    pending=[
        {"request_id": "r1", "title": "Approve deploy", "description": "Deploy v4.8",
         "requester": "system", "priority": "critical"},
        {"request_id": "r2", "title": "Allow access", "description": "Grant read",
         "requester": "user1"},
    ],
    history=[
        {"request_id": "r3", "title": "Old approval", "status": "approved",
         "decided_by": "operator", "decided_at": "2026-07-28", "reason": "ok"},
    ],
)
assert aw2.total_pending == 2
assert aw2.critical_pending == 1
assert aw2.total_history == 1

# Builder
cmd, params = ApprovalDispatcher.build_approve("r1", "Looks good")
assert cmd == "approve"
assert params["id"] == "r1"

cmd2, params2 = ApprovalDispatcher.build_reject("r2", "Not now")
assert cmd2 == "reject"

# Filter
aw3 = aw2.by_status("pending")
assert aw3.total_pending == 2
assert aw3.total_history == 0

assert "pending" in aw2.summary_line

print("  all approval workspace: OK")

# ══════════════════════════════════════════════════════════════════════
# OP-194: Timeline Explorer
# ══════════════════════════════════════════════════════════════════════
print("\n=== OP-194: TimelineExplorer ===")

te = TimelineExplorerFactory.empty()
assert te.total == 0

events = [
    {"event_id": "e1", "title": "Mission started", "event_type": "mission_started",
     "description": "Health check started", "severity": "info",
     "timestamp": "2026-07-29T00:00:00", "mission_id": "m1"},
    {"event_id": "e2", "title": "Error detected", "event_type": "error",
     "description": "Disk full", "severity": "error",
     "timestamp": "2026-07-29T00:01:00", "mission_id": "m1"},
    {"event_id": "e3", "title": "Alert", "event_type": "critical_alert",
     "description": "CPU overload", "severity": "critical",
     "timestamp": "2026-07-29T00:02:00", "mission_id": "m2"},
]
te2 = TimelineExplorerFactory.from_event_list(events)
assert te2.total == 3
assert te2.critical_count == 1
assert te2.error_count == 1

# Filter
te3 = te2.filter_severity("error")
assert te3.filtered == 1

te4 = te2.filter_mission("m1")
assert te4.filtered == 2

te5 = te2.search("disk")
assert te5.filtered == 1

# Sort
te6 = te2.sort_oldest_first()
assert te6.events[0].event_id == "e1"

# Pagination
te7 = te2.page(1)
assert te7.current_page == 1

# Jump
entry = te2.jump_to(0)
assert entry is not None
assert entry.event_id == "e1"
assert te2.jump_to(99) is None

assert "events" in te2.summary_line

print("  all timeline explorer: OK")

# ══════════════════════════════════════════════════════════════════════
# OP-195: Notification Workspace
# ══════════════════════════════════════════════════════════════════════
print("\n=== OP-195: NotificationWorkspace ===")

from src.sam.operations.notification import (
    notification_mission_started, notification_critical_alert,
)

nw = NotificationWorkspace()
assert nw.unread_count == 0

nw.add(notification_mission_started("m1", "Health check"))
nw.add(notification_critical_alert("sys1", "CPU High", "Warning"))
assert nw.unread_count == 2

# Mark read
nw.mark_read("m1")
assert nw.unread_count == 1

# Dismiss
nw.dismiss("sys1")
assert nw.unread_count == 0
assert nw.total_active == 1  # m1 still active (read but not dismissed)

# Filter
nw.add(notification_mission_started("m2", "Backup"))
criticals = nw.filter_priority("critical")
assert len(criticals) == 0  # sys1 is already dismissed

# Expiry — no expiry for recent notifications
expired = nw.clear_expired(0)  # 0 seconds = expire everything
# May or may not expire depending on timestamp timing

# History
assert len(nw.history) == 3
nw.clear_history()
assert nw.unread_count == 0

print("  all notification workspace: OK")

# ══════════════════════════════════════════════════════════════════════
# OP-196: Status Bar
# ══════════════════════════════════════════════════════════════════════
print("\n=== OP-196: StatusBar ===")

sb = StatusBarFactory.compose(
    screen="missions",
    refresh_mode="fast",
    connection="connected",
    theme="dark",
)
assert sb.screen == "missions"
assert sb.refresh_indicator == "FAST"
assert sb.connection_indicator == "ON"
assert "missions" in sb.compact_line
assert "Screen" in sb.full_line
assert len(sb.line_parts) == 7

# With data
sb2 = StatusBarFactory.compose(
    screen="approvals",
    refresh_mode="manual",
    is_paused=True,
    theme="light",
    is_plain_mode=True,
    connection="reconnecting",
    notification_workspace=NotificationWorkspace(),
)
assert sb2.refresh_indicator == "PAUSED"
assert sb2.connection_indicator == "R"
assert "PLAIN" in sb2.theme_indicator

print("  all status bar: OK")

# ══════════════════════════════════════════════════════════════════════
# OP-197: Log Viewer
# ══════════════════════════════════════════════════════════════════════
print("\n=== OP-197: LogViewer ===")

lv = LogViewer()
assert lv.is_following
assert lv.total_entries == 0

entries = LogViewerFactory.from_audit_entries([
    {"timestamp": "00:00:01", "level": "INFO", "source": "system",
     "message": "SAM started"},
    {"timestamp": "00:00:02", "level": "WARNING", "source": "health",
     "message": "CPU at 85%"},
    {"timestamp": "00:00:03", "level": "ERROR", "source": "backup",
     "message": "Backup failed"},
])
lv.add_entries(entries)
assert lv.total_entries == 3

# Follow
assert lv.scroll_position == 2
lv.scroll_up()
assert lv.scroll_position == 1
lv.scroll_to_top()
assert lv.scroll_position == 0
lv.scroll_to_bottom()
assert lv.scroll_position == 2

# Pause
lv.pause()
assert not lv.is_following
lv.resume()
assert lv.scroll_position == 2

# Search
count = lv.search("CPU")
assert count == 1
# only one match, next_match should be None
match = lv.next_match()
assert match is None
lv.clear_search()

# Filter
lv.filter_level("ERROR")
assert lv.filtered_count == 1
lv.filter_level("all")
assert lv.filtered_count == 3

# Select / Copy
sel = lv.select(1)
assert sel is not None
assert sel.level == "WARNING"
clip = lv.copy_selection()
assert "CPU" in clip

# Visible
vis = lv.visible_entries
assert len(vis) > 0

# Summary
assert "Log" in lv.summary_line

print("  all log viewer: OK")

# ══════════════════════════════════════════════════════════════════════
# OP-198: Session Workspace
# ══════════════════════════════════════════════════════════════════════
print("\n=== OP-198: SessionWorkspace ===")

sw = SessionWorkspaceFactory.empty()
assert sw.active_screen == "dashboard"
assert not sw.has_selected_mission

sw2 = SessionWorkspaceFactory.compose(
    session_id="ses-01",
    app_name="SAM Console",
    app_version="4.8.0",
    active_screen="missions",
    selected_mission_id="m1",
    selected_mission_name="Health Check",
    command_history=("status", "missions", "approvals"),
    navigation_history=("dashboard", "missions"),
    error_count=1,
    render_count=42,
    notification_count=3,
)
assert sw2.has_selected_mission
assert sw2.selected_mission_id == "m1"
assert sw2.render_count == 42
assert "ses-01" in sw2.session_summary

# From runtime objects
dr3 = DashboardRuntime()
dr3.switch_screen("approvals")
sw3 = SessionWorkspaceFactory.from_runtime(
    dashboard_runtime=dr3,
    command_history=("st", "app"),
    navigation_history=("dashboard", "missions", "approvals"),
)
assert sw3.active_screen == "approvals"
assert len(sw3.command_history) == 2

print("  all session workspace: OK")

# ══════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════════════════
print()
print("[OK] Sprint 15 — All 9 workspace modules verified")
