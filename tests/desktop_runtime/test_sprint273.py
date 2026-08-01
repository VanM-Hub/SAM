"""Sprint 273 - Desktop Workspace test."""
import unittest

from sam.desktop_runtime.workspace.dock_manager import DockManager
from sam.desktop_runtime.workspace.workspace_layout import WorkspaceLayout
from sam.desktop_runtime.workspace.workspace_model import WorkspaceModel
from sam.desktop_runtime.workspace.workspace_session import WorkspaceSession
from sam.desktop_runtime.workspace.workspace_state import WorkspaceState
from sam.desktop_runtime.workspace.workspace_validator import WorkspaceValidator


class TestWorkspaceModel(unittest.TestCase):
    def test_model_defaults(self):
        m = WorkspaceModel()
        self.assertEqual(m.workspace_id, "main")
        self.assertEqual(m.layout, "default")
        self.assertEqual(m.panels, ())
        self.assertEqual(m.active_panel, "")

    def test_model_immutable(self):
        m = WorkspaceModel()
        with self.assertRaises(Exception):
            m.name = "x"

    def test_model_with_panels(self):
        m = WorkspaceModel().with_panels("Mission", "Runtime")
        self.assertEqual(m.panels, ("Mission", "Runtime"))
        self.assertEqual(WorkspaceModel().panels, ())

    def test_model_with_active(self):
        m = WorkspaceModel().with_panels("Mission", "Runtime").with_active("Mission")
        self.assertEqual(m.active_panel, "Mission")

    def test_model_as_dict(self):
        m = WorkspaceModel().with_panels("Mission")
        dd = m.as_dict()
        self.assertEqual(dd["panels"], ["Mission"])
        self.assertIn("layout", dd)


class TestWorkspaceLayout(unittest.TestCase):
    def test_layout_default(self):
        l = WorkspaceLayout()
        self.assertEqual(l.name, "default")
        self.assertEqual(l.regions, {})

    def test_layout_with_region(self):
        l = WorkspaceLayout().with_region("left", 2)
        self.assertIn("left", l.region_names)
        self.assertEqual(l.regions["left"][1], 2)

    def test_layout_immutable_regions(self):
        l = WorkspaceLayout().with_region("left")
        base = WorkspaceLayout()
        self.assertEqual(base.regions, {})

    def test_layout_as_dict(self):
        l = WorkspaceLayout().with_region("top", 3)
        dd = l.as_dict()
        self.assertEqual(dd["regions"]["top"]["size"], 3)


class TestWorkspaceState(unittest.TestCase):
    def test_state_default(self):
        s = WorkspaceState()
        self.assertEqual(s.docked, ())
        self.assertFalse(s.dirty)

    def test_state_with_docked(self):
        s = WorkspaceState().with_docked("Mission", "Audit")
        self.assertIn("Mission", s.visible)
        self.assertIn("Mission", s.docked)

    def test_state_immutable(self):
        s = WorkspaceState()
        with self.assertRaises(Exception):
            s.dirty = True

    def test_state_mark_dirty(self):
        s = WorkspaceState().mark_dirty()
        self.assertTrue(s.dirty)
        self.assertFalse(WorkspaceState().dirty)

    def test_state_as_dict(self):
        s = WorkspaceState().with_docked("Mission").mark_dirty()
        dd = s.as_dict()
        self.assertTrue(dd["dirty"])
        self.assertEqual(dd["docked"], ["Mission"])


class TestWorkspaceSession(unittest.TestCase):
    def test_session_default(self):
        s = WorkspaceSession()
        self.assertEqual(s.session_id, "ws-session")
        self.assertEqual(s.active_panel, "")

    def test_session_with_panels(self):
        s = WorkspaceSession(panels=("Mission", "Runtime"))
        self.assertEqual(s.active_panel, "Mission")

    def test_session_immutable(self):
        s = WorkspaceSession()
        with self.assertRaises(Exception):
            s.session_id = "x"

    def test_session_with_model(self):
        m = WorkspaceModel().with_panels("Policy").with_active("Policy")
        s = WorkspaceSession().with_model(m)
        self.assertEqual(s.active_panel, "Policy")

    def test_session_as_dict(self):
        s = WorkspaceSession(panels=("Mission",))
        dd = s.as_dict()
        self.assertIn("model", dd)
        self.assertEqual(dd["active_panel"], "Mission")


class TestWorkspaceValidator(unittest.TestCase):
    def test_valid_model(self):
        m = WorkspaceModel().with_panels("Mission").with_active("Mission")
        self.assertEqual(WorkspaceValidator.validate_model(m), [])

    def test_active_panel_not_in_panels(self):
        m = WorkspaceModel().with_panels("Mission").with_active("Runtime")
        self.assertNotEqual(WorkspaceValidator.validate_model(m), [])

    def test_empty_workspace_id(self):
        m = WorkspaceModel(workspace_id="")
        issues = WorkspaceValidator.validate_model(m)
        self.assertTrue(any("workspace_id" in i for i in issues))

    def test_duplicate_panels(self):
        issues = WorkspaceValidator.validate_panels(("A", "A"))
        self.assertTrue(any("duplikat" in i for i in issues))

    def test_empty_panel_name(self):
        issues = WorkspaceValidator.validate_panels(("",))
        self.assertTrue(any("kosong" in i for i in issues))


class TestDockManager(unittest.TestCase):
    def test_dock_adds_panel(self):
        s = DockManager.dock(WorkspaceState(), "Mission")
        self.assertIn("Mission", s.docked)
        self.assertIn("Mission", s.visible)

    def test_dock_preserves_order_dedupe(self):
        s = DockManager.dock(WorkspaceState(), "A", "B", "A")
        self.assertEqual(list(s.docked), ["A", "B"])

    def test_dock_immutable(self):
        base = WorkspaceState()
        DockManager.dock(base, "Mission")
        self.assertEqual(base.docked, ())

    def test_float_panel(self):
        s = DockManager.dock(WorkspaceState(), "Mission", "Audit")
        s2 = DockManager.float_panel(s, "Mission")
        self.assertNotIn("Mission", s2.docked)
        self.assertIn("Mission", s2.floating)
        self.assertTrue(s2.dirty)

    def test_float_non_docked_noop(self):
        s = WorkspaceState()
        s2 = DockManager.float_panel(s, "Mission")
        self.assertFalse(s2.dirty)

    def test_close_removes_everywhere(self):
        s = DockManager.dock(WorkspaceState(), "Mission", "Audit")
        s2 = DockManager.close(s, "Mission")
        self.assertNotIn("Mission", s2.docked)
        self.assertNotIn("Mission", s2.visible)
        self.assertIn("Audit", s2.visible)

    def test_dock_manager_no_io(self):
        self.assertTrue(callable(DockManager.dock))


if __name__ == "__main__":
    unittest.main()
