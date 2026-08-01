"""Sprint 274 - Desktop Panels test."""
import unittest

from sam.desktop_runtime.panels.panel_model import PanelModel
from sam.desktop_runtime.panels.panels_registry import (
    PanelsRegistry,
    default_panels,
)


class TestPanelModel(unittest.TestCase):
    def test_panel_default_title(self):
        p = PanelModel(name="Mission")
        self.assertEqual(p.title, "Mission")

    def test_panel_uses_given_title(self):
        p = PanelModel(name="Mission", title="Misi Operasional")
        self.assertEqual(p.title, "Misi Operasional")

    def test_panel_immutable(self):
        p = PanelModel(name="Mission")
        with self.assertRaises(Exception):
            p.name = "Runtime"

    def test_panel_readonly_default(self):
        p = PanelModel(name="Mission")
        self.assertTrue(p.readonly)

    def test_panel_as_dict(self):
        p = PanelModel(name="Mission", source_runtime="Mission Runtime")
        dd = p.as_dict()
        self.assertEqual(dd["name"], "Mission")
        self.assertEqual(dd["source_runtime"], "Mission Runtime")
        self.assertTrue(dd["readonly"])


class TestPanelsRegistry(unittest.TestCase):
    def test_default_empty(self):
        r = PanelsRegistry()
        self.assertEqual(len(r), 0)

    def test_register(self):
        r = PanelsRegistry().register(PanelModel(name="Mission"))
        self.assertEqual(len(r), 1)
        self.assertEqual(r.names, ("Mission",))

    def test_register_immutable(self):
        base = PanelsRegistry()
        base.register(PanelModel(name="Mission"))
        self.assertEqual(len(base), 0)

    def test_register_all(self):
        r = PanelsRegistry().register_all(default_panels())
        self.assertEqual(len(r), 10)

    def test_get_existing(self):
        r = PanelsRegistry().register(PanelModel(name="Mission"))
        self.assertIsNotNone(r.get("Mission"))
        self.assertEqual(r.get("Mission").name, "Mission")

    def test_get_missing(self):
        r = PanelsRegistry()
        self.assertIsNone(r.get("Nope"))

    def test_as_dict(self):
        r = PanelsRegistry().register(PanelModel(name="Mission"))
        dd = r.as_dict()
        self.assertEqual(len(dd["panels"]), 1)

    def test_get_returns_model_as_dict(self):
        r = PanelsRegistry().register(PanelModel(name="Mission"))
        self.assertEqual(r.get("Mission").as_dict()["name"], "Mission")


class TestDefaultPanels(unittest.TestCase):
    def test_ten_panels(self):
        self.assertEqual(len(default_panels()), 10)

    def test_required_panels_present(self):
        names = [p.name for p in default_panels()]
        for required in ("Mission", "Runtime", "Memory", "Knowledge",
                         "Workflow", "Policy", "Audit", "Artifact",
                         "Provider", "Execution"):
            self.assertIn(required, names)

    def test_all_readonly(self):
        for p in default_panels():
            self.assertTrue(p.readonly, f"{p.name} harus read-only")

    def test_all_source_runtime(self):
        for p in default_panels():
            self.assertNotEqual(p.source_runtime, "",
                                f"{p.name} harus punya source runtime")

    def test_no_duplicate_names(self):
        names = [p.name for p in default_panels()]
        self.assertEqual(len(names), len(set(names)))

    def test_no_provider_specific(self):
        names = [p.name.lower() for p in default_panels()]
        for prov in ("openai", "anthropic", "gemini", "deepseek", "ollama"):
            self.assertNotIn(prov, names)

    def test_registry_from_default(self):
        r = PanelsRegistry().register_all(default_panels())
        self.assertIn("Execution", r.names)


if __name__ == "__main__":
    unittest.main()
