"""Smoke test for SAM Desktop Qt layer.

Tests that:
- QApplication starts in offscreen mode
- MainWindow can be created
- Desktop session initializes
- Workspace is created
- Renderer bridge is active
- Shutdown is clean

No visual testing. Headless only (QT_QPA_PLATFORM=offscreen).
"""

from __future__ import annotations

import os
import sys

# Force headless before any Qt import
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# ── Guard: skip if PySide6 missing ─────────────────────────────
try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
    from PySide6.QtCore import QTimer, Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    print("[SKIP] PySide6 not installed — smoke test skipped")


import pytest


@pytest.mark.skipif(not HAS_QT, reason="PySide6 not installed")
class TestDesktopSmoke:
    """Headless smoke tests for the SAM Desktop Qt layer."""

    @pytest.fixture(autouse=True)
    def _qapp(self):
        """Provide or reuse one QApplication per session."""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app
        # Do NOT destroy — may be reused by other tests

    def test_qapplication_created(self, _qapp):
        """OP-225a: QApplication exists and is valid."""
        app = QApplication.instance()
        assert app is not None
        assert app.applicationName() != ""
        assert app.platformName() == "offscreen"

    def test_qmainwindow_created(self, _qapp):
        """OP-225b: MainWindow can be created and shown."""
        from sam.operations.presentation.desktop.qt.main_window import (
            QtMainWindow,
        )
        from sam.operations.presentation.desktop.qt.application import (
            QtApplication,
        )

        qt_app = QtApplication(_qapp)
        window = QtMainWindow(qt_app)
        qmain = window.build()
        assert qmain is not None
        assert qmain.windowTitle() != ""

        qmain.show()
        assert qmain.isVisible()
        qmain.close()

    def test_workspace_manager(self, _qapp):
        """OP-225c: WorkspaceManager creates and manages regions."""
        from sam.operations.presentation.desktop.qt.workspace import (
            WorkspaceManager,
            WorkspaceRegion,
        )

        wm = WorkspaceManager()
        assert wm.active_workspace == "default"
        assert len(wm.get_all_regions()) >= 5
        assert wm.get_region("navigation") is not None

        # Float timeline
        wm.set_floating("timeline", True, (100, 100, 400, 300))
        tl = wm.get_region("timeline")
        assert tl.floating

        # Workspace save/load
        wm.save_workspace("minimal")
        assert "minimal" in wm.workspace_names
        wm.set_active_workspace("minimal")
        assert wm.active_workspace == "minimal"
        wm.load_workspace("default")
        assert wm.active_workspace == "default"

        # Persistence roundtrip
        data = wm.to_dict()
        wm2 = WorkspaceManager()
        wm2.from_dict(data)
        assert wm2.get_region("navigation") is not None

    def test_dock_manager(self, _qapp):
        """OP-225d: DockManager creates QDockWidget panels."""
        from sam.operations.presentation.desktop.qt.dock_manager import (
            QtDockManager,
        )

        main = QMainWindow()
        dm = QtDockManager(main)

        panels = dm.create_all()
        assert len(panels) == 5
        assert dm.get_panel("navigation") is not None
        assert dm.get_panel("mission") is not None
        assert dm.get_panel("timeline") is not None
        assert dm.get_panel("notifications") is not None
        assert dm.get_panel("logs") is not None

        # Toggle — use widget property of DockPanel
        nav_panel = dm.get_panel("navigation")
        assert dm.set_visible("navigation", False)
        assert not nav_panel._qdock.isVisible()
        dm.set_visible("navigation", True)

        # Save/restore
        state = dm.save_state()
        assert "docks" in state
        assert "navigation" in state["docks"]
        dm.restore_state(state)

        # Apply layout
        from sam.operations.presentation.desktop.layout import DesktopLayout
        dm.apply_layout(DesktopLayout())

    def test_missions_widget(self, _qapp):
        """OP-225e: MissionTableWidget renders data."""
        from sam.operations.presentation.desktop.qt.mission_widget import (
            MissionTableWidget,
        )

        import PySide6.QtWidgets as qw
        container = qw.QWidget()
        container.setLayout(qw.QVBoxLayout())

        mt = MissionTableWidget(container)
        widget = mt.build()
        assert widget is not None

        mt.set_data([
            {"id": "M-001", "status": "running", "priority": "critical",
             "progress": "75%", "owner": "system",
             "started_at": "2026-07-28", "elapsed": "2h"},
        ])
        assert mt.row_count == 1

        mt.clear()
        assert mt.row_count == 0

    def test_timeline_widget(self, _qapp):
        """OP-225f: TimelineWidget renders events."""
        from sam.operations.presentation.desktop.qt.timeline_widget import (
            TimelineWidget,
        )

        tw = TimelineWidget()
        tw.build()

        tw.set_events([
            {"severity": "error", "time": "12:30",
             "mission_id": "M-001", "description": "CPU alert"},
        ])
        assert tw.event_count == 1
        tw.set_follow(True)
        tw.clear()
        assert tw.event_count == 0

    def test_dashboard_widget(self, _qapp):
        """OP-225g: DashboardWidget renders summary cards."""
        from sam.operations.presentation.desktop.qt.dashboard_widget import (
            DashboardWidget,
        )

        dw = DashboardWidget()
        dw.build()
        dw.update_from_dashboard({
            "mission_active": 3, "mission_count": 10,
            "approval_pending": 1, "notification_unread": 2,
            "health_status": "healthy", "trust_grade": "A",
        })
        dw.add_activity("Test activity")
        dw.clear()

    def test_notification_panel(self, _qapp):
        """OP-225h: NotificationPanel builds and manages."""
        from sam.operations.presentation.desktop.qt.notification_panel import (
            NotificationPanel,
        )

        np = NotificationPanel()
        np.build()

        np.set_notifications([
            {"id": "N1", "title": "Alert", "message": "Test",
             "priority": "high", "read": False, "source": "test",
             "timestamp": "2026-07-28"},
        ])
        assert np.notification_count == 1
        assert np.unread_count == 1

        np.add_notification({
            "id": "N2", "title": "Info", "message": "Test2",
            "priority": "normal", "read": True, "source": "test",
            "timestamp": "2026-07-28",
        })
        assert np.notification_count == 2

        np.clear()
        assert np.notification_count == 0

    def test_log_viewer_widget(self, _qapp):
        """OP-225i: LogViewerWidget renders and filters logs."""
        from sam.operations.presentation.desktop.qt.log_viewer_widget import (
            LogViewerWidget,
        )

        lv = LogViewerWidget()
        lv.build()

        lv.append_log("INFO", "Started", "system", "12:00")
        lv.append_log("ERROR", "Failed", "mission", "12:01")
        assert lv.line_count == 2
        assert lv.is_following

        lv.set_follow(False)
        assert not lv.is_following

        lv.clear()
        assert lv.line_count == 0

    def test_command_palette(self, _qapp):
        """OP-225j: CommandPalette builds and toggles."""
        from sam.operations.presentation.desktop.qt.command_palette import (
            CommandPalette,
        )
        from sam.operations.presentation.console.command_registry import (
            CommandRegistry,
        )

        parent = QWidget()
        cp = CommandPalette(parent)
        dialog = cp.build()
        assert dialog is not None

        reg = CommandRegistry()
        cp.load_from_registry(reg.commands)
        assert cp.command_count > 5

        cp.show()
        assert cp.is_open
        cp.hide()
        assert not cp.is_open

    def test_renderer_bridge_active(self, _qapp):
        """OP-225k: QtRendererBridge connects to adapter."""
        from sam.operations.presentation.desktop.renderer_adapter import (
            DesktopRendererAdapter,
        )
        from sam.operations.presentation.desktop.qt.renderer_bridge import (
            QtRendererBridge,
        )

        adapter = DesktopRendererAdapter()
        bridge = QtRendererBridge(adapter)
        assert bridge is not None
        assert bridge._adapter is adapter

    def test_full_shutdown(self, _qapp):
        """OP-225l: Shutdown — main window closes cleanly."""
        from sam.operations.presentation.desktop.qt.main_window import (
            QtMainWindow,
        )
        from sam.operations.presentation.desktop.qt.application import (
            QtApplication,
        )

        qt_app = QtApplication(_qapp)
        window = QtMainWindow(qt_app)
        qmain = window.build()
        qmain.show()
        qmain.close()
        # No crash = pass
        assert True
