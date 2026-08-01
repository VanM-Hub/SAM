"""Sprint 276 - Desktop Runtime test."""
import unittest

from sam.desktop_runtime.conversation.bridge import ConversationBridge
from sam.desktop_runtime.dashboard_bridge.bridge import DashboardBridge
from sam.desktop_runtime.panels.panels_registry import (
    PanelsRegistry,
    default_panels,
)
from sam.desktop_runtime.runtime.desktop_controller import DesktopController
from sam.desktop_runtime.runtime.desktop_coordinator import DesktopCoordinator
from sam.desktop_runtime.runtime.desktop_pipeline import DesktopPipeline
from sam.desktop_runtime.runtime.desktop_runtime import DesktopRuntime
from sam.desktop_runtime.runtime.desktop_summary import DesktopSummary
from sam.desktop_runtime.workspace.workspace_model import WorkspaceModel
from sam.desktop_runtime.workspace.workspace_state import WorkspaceState


class TestDesktopController(unittest.TestCase):
    def test_build_session(self):
        m = WorkspaceModel().with_panels("Mission")
        s = DesktopController.build_session(m)
        self.assertEqual(s.panels, ("Mission",))
        self.assertEqual(s.active_panel, "Mission")

    def test_validate_valid(self):
        m = WorkspaceModel().with_panels("Mission").with_active("Mission")
        self.assertEqual(DesktopController.validate(m), [])

    def test_validate_invalid(self):
        m = WorkspaceModel().with_panels("Mission").with_active("Runtime")
        self.assertNotEqual(DesktopController.validate(m), [])

    def test_compose_dashboard(self):
        reg = PanelsRegistry().register_all(default_panels())
        dash = DesktopController.compose_dashboard(reg)
        self.assertEqual(len(dash.cards), 10)

    def test_panel_titles(self):
        reg = PanelsRegistry().register_all(default_panels())
        self.assertIn("Execution", DesktopController.panel_titles(reg))


class TestDesktopCoordinator(unittest.TestCase):
    def test_modes(self):
        m = DesktopCoordinator.modes(ConversationBridge(), DashboardBridge())
        self.assertIn("conversation", m)
        self.assertIn("dashboard", m)

    def test_assemble_visible(self):
        s = DesktopCoordinator.assemble(WorkspaceState(), DesktopController, "Mission")
        self.assertIn("Mission", s.visible)

    def test_assemble_immutable(self):
        base = WorkspaceState()
        DesktopCoordinator.assemble(base, DesktopController, "Mission")
        self.assertEqual(base.visible, ())

    def test_ready_conversation(self):
        self.assertTrue(DesktopCoordinator.ready_conversation(ConversationBridge()))

    def test_ready_dashboard(self):
        self.assertTrue(DesktopCoordinator.ready_dashboard(DashboardBridge()))


class TestDesktopPipeline(unittest.TestCase):
    def test_stages(self):
        p = DesktopPipeline()
        self.assertEqual(p.first, "foundation")
        self.assertEqual(p.last, "integration")
        self.assertIn("panels", p.stages)

    def test_pipeline_as_dict(self):
        p = DesktopPipeline()
        self.assertIn("workspace", p.as_dict()["stages"])

    def test_pipeline_immutable(self):
        p = DesktopPipeline()
        with self.assertRaises(Exception):
            p.stages = ()


class TestDesktopSummary(unittest.TestCase):
    def test_summary_defaults(self):
        s = DesktopSummary()
        self.assertEqual(s.runtime, "desktop_runtime")
        self.assertEqual(s.version, "29.0.0")
        self.assertTrue(s.read_only)
        self.assertFalse(s.execute_self)

    def test_summary_immutable(self):
        s = DesktopSummary()
        with self.assertRaises(Exception):
            s.read_only = False

    def test_summary_as_dict(self):
        s = DesktopSummary(panels=("Mission",), dashboard_cards=1)
        dd = s.as_dict()
        self.assertEqual(dd["version"], "29.0.0")
        self.assertEqual(dd["dashboard_cards"], 1)


class TestDesktopRuntime(unittest.TestCase):
    def test_runtime_defaults(self):
        r = DesktopRuntime()
        expected = [p.name for p in default_panels()]
        self.assertEqual(list(r.registry.names), expected)
        self.assertTrue(r.contract.composition_only)

    def test_runtime_immutable(self):
        r = DesktopRuntime()
        with self.assertRaises(Exception):
            r._model = WorkspaceModel()

    def test_runtime_run(self):
        r = DesktopRuntime()
        snap = r.run()
        self.assertEqual(len(snap.card_titles()), 10)

    def test_runtime_summary(self):
        r = DesktopRuntime()
        s = r.snapshot_summary()
        self.assertEqual(s.dashboard_cards, 10)

    def test_runtime_pipeline(self):
        r = DesktopRuntime()
        self.assertIn("dashboard", r.pipeline_stages())

    def test_runtime_as_dict(self):
        r = DesktopRuntime()
        dd = r.as_dict()
        self.assertFalse(dd["execute_self"])
        self.assertTrue(dd["preview_only"])

    def test_runtime_invalid_raises(self):
        r = DesktopRuntime(model=WorkspaceModel().with_active("Nope"))
        with self.assertRaises(ValueError):
            r.run()


if __name__ == "__main__":
    unittest.main()
