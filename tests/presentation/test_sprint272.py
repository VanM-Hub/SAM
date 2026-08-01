"""Sprint 272 - Presentation Layer Foundation test."""
import unittest

from sam.presentation.bridge import PresentationLayerBridge
from sam.presentation.conversation.bridge import ConversationBridge
from sam.presentation.dashboard_bridge.bridge import DashboardBridge
from sam.presentation.foundation.capability import PresentationCapability
from sam.presentation.foundation.contract import PresentationContract
from sam.presentation.foundation.descriptor import PresentationDescriptor
from sam.presentation.foundation.metadata import PresentationMetadata
from sam.presentation.foundation.registry import (
    PresentationRegistry,
    KNOWN_COMPONENTS,
)


class TestDescriptor(unittest.TestCase):
    def test_descriptor_immutable(self):
        d = PresentationDescriptor()
        with self.assertRaises(Exception):
            d.name = "x"  # frozen
        self.assertEqual(d.name, "presentation")
        self.assertEqual(d.version, "29.0.0")

    def test_descriptor_as_dict(self):
        d = PresentationDescriptor()
        dd = d.as_dict()
        self.assertEqual(dd["kind"], "desktop")
        self.assertIn("layers", dd)
        self.assertIn("workspace", dd["layers"])

    def test_descriptor_description_no_execute(self):
        d = PresentationDescriptor()
        self.assertIn("tanpa eksekusi sendiri", d.description)


class TestMetadata(unittest.TestCase):
    def test_metadata_program_f(self):
        m = PresentationMetadata()
        self.assertEqual(m.program, "F")
        self.assertEqual(m.version, "29.0.0")
        self.assertEqual(list(m.sprints), [272, 273, 274, 275, 276, 277, 278, 279])
        self.assertEqual(m.branch, "phase-xxix")


class TestCapability(unittest.TestCase):
    def test_capability_modes(self):
        c = PresentationCapability()
        self.assertTrue(c.visualize)
        self.assertTrue(c.compose_workspace)
        self.assertTrue(c.present_panels)
        self.assertTrue(c.render_dashboard)
        self.assertTrue(c.certify)
        self.assertFalse(c.execute_self)
        self.assertIn("panels", c.supported_modes)

    def test_capability_no_execute(self):
        c = PresentationCapability()
        self.assertFalse(c.execute_self)


class TestContract(unittest.TestCase):
    def test_contract_constraints(self):
        c = PresentationContract()
        self.assertTrue(c.preview_only)
        self.assertTrue(c.deterministic)
        self.assertTrue(c.synchronous)
        self.assertTrue(c.composition_only)
        self.assertFalse(c.execute_self)
        self.assertFalse(c.inference)
        self.assertFalse(c.llm)
        self.assertEqual(c.external_calls, 0)

    def test_contract_forbidden(self):
        c = PresentationContract()
        for item in ("async", "thread", "multiprocessing", "socket",
                     "requests", "httpx", "subprocess"):
            self.assertIn(item, c.forbidden)


class TestRegistry(unittest.TestCase):
    def test_default_empty(self):
        r = PresentationRegistry()
        self.assertEqual(len(r), 0)

    def test_with_entry_immutable(self):
        r = PresentationRegistry().with_entry("Panels", "component")
        self.assertEqual(len(r), 1)
        self.assertEqual(r.names, ("Panels",))
        base = PresentationRegistry()
        self.assertEqual(len(base), 0)

    def test_known_components_present(self):
        for name in ("Workspace", "Panels", "Dashboard", "Runtime",
                     "Monitoring", "Certification", "Integration"):
            self.assertIn(name, KNOWN_COMPONENTS)

    def test_registry_as_dict(self):
        r = PresentationRegistry().with_entry("Panels", "component")
        dd = r.as_dict()
        self.assertEqual(dd["entries"], ["Panels"])
        self.assertEqual(dd["descriptor"]["kind"], "desktop")


class TestBridges(unittest.TestCase):
    def test_conversation_bridge_readonly(self):
        b = ConversationBridge()
        self.assertTrue(b.read_only())
        self.assertIn("conversation", b.scope())
        self.assertTrue(b.as_dict()["read_only"])

    def test_dashboard_bridge_readonly(self):
        b = DashboardBridge()
        self.assertTrue(b.read_only())
        self.assertIn("dashboard", b.scope())
        self.assertTrue(b.as_dict()["read_only"])

    def test_runtime_bridge_readonly(self):
        rb = PresentationLayerBridge()
        self.assertTrue(rb.read_only())
        self.assertIn("conversation", rb.modes())
        self.assertIn("dashboard", rb.modes())
        self.assertTrue(rb.as_dict()["read_only"])

    def test_runtime_bridge_dict_has_both(self):
        rb = PresentationLayerBridge()
        dd = rb.as_dict()
        self.assertIn("conversation", dd)
        self.assertIn("dashboard", dd)

    def test_bridge_frozen(self):
        rb = PresentationLayerBridge()
        with self.assertRaises(Exception):
            rb.conversation = ConversationBridge()


class TestNoIOLayers(unittest.TestCase):
    def test_forbidden_imports_absent(self):
        import ast
        from pathlib import Path
        src = Path(__file__).resolve().parents[2] / "src"
        desktop_py = list((src / "sam" / "presentation").rglob("*.py"))
        self.assertGreater(len(desktop_py), 0)
        banned = ("import asyncio", "import threading", "import multiprocessing",
                  "import socket", "import subprocess", "import requests",
                  "import httpx")
        found = []
        for p in desktop_py:
            if p.name == "__init__.py":
                continue
            tree = ast.parse(p.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        if a.name in ("asyncio", "threading", "multiprocessing",
                                      "socket", "subprocess", "requests",
                                      "httpx"):
                            found.append(a.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    root = node.module.split(".")[0]
                    if root in ("asyncio", "threading", "multiprocessing",
                                "socket", "subprocess", "requests", "httpx"):
                        found.append(root)
        self.assertEqual(found, [], f"forbidden imports found: {found}")


if __name__ == "__main__":
    unittest.main()
