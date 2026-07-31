"""Sprint 261 - Intelligence Runtime Foundation test."""
import unittest

from sam.intelligence_runtime.capability import IntelligenceCapability
from sam.intelligence_runtime.contract import IntelligenceContract
from sam.intelligence_runtime.conversation_bridge import ConversationBridge
from sam.intelligence_runtime.dashboard_bridge import DashboardBridge
from sam.intelligence_runtime.descriptor import IntelligenceDescriptor
from sam.intelligence_runtime.metadata import IntelligenceMetadata
from sam.intelligence_runtime.registry import (
    IntelligenceRegistry,
    KNOWN_RUNTIMES,
)


class TestDescriptor(unittest.TestCase):
    def test_descriptor_immutable(self):
        d = IntelligenceDescriptor()
        with self.assertRaises(Exception):
            d.name = "x"  # frozen
        self.assertEqual(d.name, "intelligence_runtime")
        self.assertEqual(d.version, "28.0.0")

    def test_descriptor_as_dict(self):
        d = IntelligenceDescriptor()
        dd = d.as_dict()
        self.assertEqual(dd["kind"], "unified_intelligence")
        self.assertIn("layers", dd)


class TestMetadata(unittest.TestCase):
    def test_metadata_program_e(self):
        m = IntelligenceMetadata()
        self.assertEqual(m.program, "E")
        self.assertEqual(m.version, "28.0.0")
        self.assertEqual(list(m.sprints), [261, 262, 263, 264, 265, 266, 267, 268])


class TestCapability(unittest.TestCase):
    def test_capability_modes(self):
        c = IntelligenceCapability()
        self.assertTrue(c.assemble_context)
        self.assertTrue(c.validate_runtime)
        self.assertTrue(c.build_graph)
        self.assertTrue(c.certify)
        self.assertTrue(c.monitor)
        self.assertTrue(c.bundle)
        self.assertIn("context", c.supported_modes)


class TestContract(unittest.TestCase):
    def test_contract_constraints(self):
        c = IntelligenceContract()
        self.assertTrue(c.preview_only)
        self.assertTrue(c.deterministic)
        self.assertTrue(c.synchronous)
        self.assertFalse(c.inference)
        self.assertFalse(c.llm)
        self.assertEqual(c.external_calls, 0)


class TestRegistry(unittest.TestCase):
    def test_default_empty(self):
        r = IntelligenceRegistry()
        self.assertEqual(len(r), 0)

    def test_with_entry_immutable(self):
        r = IntelligenceRegistry().with_entry("Mission", "runtime")
        self.assertEqual(len(r), 1)
        self.assertEqual(r.names, ("Mission",))
        base = IntelligenceRegistry()
        self.assertEqual(len(base), 0)

    def test_known_runtimes_present(self):
        for name in ("Guardian", "Decision", "Approval", "Execution",
                     "Runtime Kernel", "Connector", "Orchestrator",
                     "Mission", "Provider", "Agent", "Skills", "Memory",
                     "Knowledge", "Cognitive", "Workflow", "Policy",
                     "Audit", "Artifact", "Model Runtime",
                     "Execution Runtime", "Runtime Service"):
            self.assertIn(name, KNOWN_RUNTIMES)

    def test_known_runtimes_no_provider_hardcode(self):
        providers = ("openai", "anthropic", "gemini", "deepseek",
                     "ollama", "openrouter")
        for name in KNOWN_RUNTIMES:
            self.assertNotIn(name.lower(), providers)


class TestBuilder(unittest.TestCase):
    def test_builder_register_known(self):
        from sam.intelligence_runtime.builder import IntelligenceBuilder
        reg = IntelligenceBuilder.create().register_known_runtimes().build()
        self.assertEqual(len(reg), len(KNOWN_RUNTIMES))
        self.assertIn("Runtime Service", reg.names)

    def test_build_empty(self):
        from sam.intelligence_runtime.builder import IntelligenceBuilder
        reg = IntelligenceBuilder.create().build()
        self.assertEqual(len(reg), 0)


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


if __name__ == "__main__":
    unittest.main()
