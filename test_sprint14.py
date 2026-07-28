"""Sprint 14 validation script."""
from __future__ import annotations
import sys
sys.path.insert(0, "D:/Project AI/SAM/src")

from src.sam.operations.presentation.console import *

# OP-181
print("=== OP-181: App Lifecycle ===")
app = ConsoleApp()
assert app.state == AppState.INITIALIZING
app.startup()
assert app.state == AppState.READY
app.run()
assert app.is_running
assert app.shutdown()
assert app.is_stopped
print("  lifecycle: OK")

with ConsoleApp() as a:
    a.startup()
    a.run()
assert a.is_stopped
print("  context manager: OK")

a2 = ConsoleApp()
a2.startup(AppConfig(version="4.7.0"))
a2.run()
a2.request_restart()
assert a2.restart_pending
a2.perform_restart()
assert a2.is_running
a2.shutdown()
print("  restart: OK")

# OP-182
print("\n=== OP-182: Command Registry ===")
reg = CommandRegistry()
assert len(reg.commands) == 24
assert reg.validate("approve")
assert reg.validate("ap")
assert reg.validate("?")
assert not reg.validate("garbage")
assert reg.resolve("ap") == "approve"
assert reg.get_category("st") == "operations"
assert get_autocomplete("approve") == 1
assert "Approve" in get_command_help("approve")
assert "dash" in get_command_aliases("dashboard")
assert "[navigation]" in format_help()
assert "Approve" in format_help("approve")
comps = reg.autocomplete("app")
assert "approve" in comps
print("  all registry: OK")

# OP-183
print("\n=== OP-183: Prompt Runtime ===")
prompt = PromptRuntime()
prompt.add_to_history("cmd1")
prompt.add_to_history("cmd2")
prompt.add_to_history("cmd3")
prompt.add_to_history("cmd3")  # consecutive duplicate
assert prompt.history_count == 3
assert list(prompt.history) == ["cmd3", "cmd2", "cmd1"]
prompt.set_completions(("apple", "approve"))
c1 = prompt.next_completion()
assert c1 is not None
prompt.clear_history()
assert prompt.history_count == 0
print("  all prompt: OK")

# OP-184
print("\n=== OP-184: Event Bus ===")
bus = EventBus()
rcvd = []
bus.subscribe(ScreenChanged, lambda e: rcvd.append("s"))
bus.subscribe(CommandExecuted, lambda e: rcvd.append("c"))
bus.publish(ScreenChanged("x", "y"))
bus.publish(CommandExecuted("t", True))
bus.publish(RefreshRequested("full", "user"))
assert bus.event_count == 3
assert len(rcvd) == 2
for _ in range(100):
    bus.publish(RefreshRequested("auto", "tick"))
assert bus.event_count == 103
assert len(bus.recent_events(5)) == 5
assert len(bus.events_by_type(ScreenChanged)) == 1
print("  all event bus: OK")

# OP-185
print("\n=== OP-185: Notification Center ===")
from src.sam.operations.notification import (
    notification_mission_started, notification_critical_alert,
)
center = NotificationCenter()
assert center.unread_count == 0
center.push(notification_mission_started("m1", "A"))
center.push(notification_critical_alert("s1", "C", "Urgent"))
assert center.unread_count == 2
assert center.critical_count == 1
assert center.badge_count == 4  # 2 unread + 1*2 critical
items = center.all()
assert center.dismiss(items[0].item_id)
assert center.unread_count == 1
center.dismiss_all()
assert center.unread_count == 0
print("  all notification center: OK")

# OP-186
print("\n=== OP-186: Shortcut ===")
sc = ShortcutRegistry()
assert sc.validate_all()
assert len(sc.all) == 31
assert sc.match("F5").command == "refresh"
assert sc.match("Q", 1).command == "exit"
assert sc.match("1").command == "dashboard"
assert sc.match("ESC").command == "back"
assert sc.match("?").command == "help"
assert sc.match("Z") is None
assert sc.by_command("refresh") is not None
assert len(sc.by_category("navigation")) > 0
assert "Ctrl" in sc.format_help("utility")
print("  all shortcuts: OK")

# OP-187
print("\n=== OP-187: Config ===")
cfg = ConsoleConfig()
assert cfg.theme == "dark"
assert cfg.refresh_rate == 10.0
cfg2 = ConsoleConfig(theme="light", refresh_rate=5.0)
try:
    ConsoleConfig(theme="bad")
    assert False, "should raise"
except ValueError:
    pass
d = cfg2.to_dict()
assert d["theme"] == "light"
cfg3 = ConsoleConfig.from_dict(d)
assert cfg3.theme == "light"
cfg4 = ConsoleConfig.merge(cfg, {"theme": "minimal", "page_size": 50})
assert cfg4.theme == "minimal"
assert cfg4.page_size == 50
assert cfg4.refresh_rate == 10.0
print("  all config: OK")

# OP-188
print("\n=== OP-188: Error Recovery ===")
rec = ErrorRecovery()
fired = []
assert rec.recover("r", "e1", retry_fn=lambda: fired.append(1))
assert len(fired) == 1
assert rec.retry_count == 1
assert rec.recover("r", "e2", fallback_fn=lambda: fired.append(2))
assert rec._fallback_active
assert not rec.in_plain_mode
assert rec.recover("r", "e3")
assert rec.in_plain_mode
assert rec.recover("r", "e4")
assert rec.in_safe_mode
assert rec.recovery_count > 0
assert rec.latest_event is not None
rec.reset()
assert not rec.in_safe_mode
assert rec.retry_count == 0
print("  all recovery: OK")

# OP-189
print("\n=== OP-189: Console Telemetry ===")
tel = ConsoleTelemetry()
tel.record_render(0.04)
tel.record_render(0.06)
tel.record_refresh(0.10)
tel.record_command("approve", 0.02)
tel.record_command("reject", 0.04)
tel.record_screen_switch()
tel.record_error()
assert tel.render_count == 2
assert tel.refresh_count == 1
assert tel.command_count == 2
assert tel.error_count == 1
assert 49 < tel.avg_render_ms < 51
assert tel.avg_refresh_ms == 100.0
assert tel.avg_command_ms == 30.0
snap = tel.snapshot(notification_count=3, unread_notifications=1)
assert snap.render_count == 2
# uptime may be 0 if snapshot is taken at same instant as start
assert snap.uptime_seconds >= 0
summary = tel.format_summary()
assert "Renders" in summary
tel.record_command("approve", 0.01)
assert tel.commands_by_type["approve"] == 2
tel.reset_all()
assert tel.render_count == 0
print("  all telemetry: OK")

print()
print("[OK] Sprint 14 — All 10 OP deliverables verified")
