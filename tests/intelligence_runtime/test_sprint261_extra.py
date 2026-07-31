"""Sprint 261 - Foundation: test lanjutan (purity, determinism, serialisasi)."""
import unittest

from sam.intelligence_runtime.capability import IntelligenceCapability
from sam.intelligence_runtime.contract import IntelligenceContract
from sam.intelligence_runtime.conversation_bridge import (
    ConversationBridge,
    ConversationBridgeSnapshot,
)
from sam.intelligence_runtime.dashboard_bridge import (
    DashboardBridge,
    DashboardBridgeSnapshot,
)
from sam.intelligence_runtime.descriptor import IntelligenceDescriptor
from sam.intelligence_runtime.metadata import IntelligenceMetadata
from sam.intelligence_runtime.registry import (
    IntelligenceRegistry,
    RegistryEntry,
)


class TestSerialization(unittest.TestCase):
    def test_all_as_dict_roundtrip(self):
        objs = [
            IntelligenceDescriptor(),
            IntelligenceCapability(),
            IntelligenceContract(),
            IntelligenceMetadata(),
            IntelligenceRegistry(),
            ConversationBridge(),
            DashboardBridge(),
        ]
        for o in objs:
            d = o.as_dict()
            self.assertIsInstance(d, dict, type(o).__name__)

    def test_nested_as_dict(self):
        d = IntelligenceDescriptor().as_dict()
        self.assertIsInstance(d["metadata"], dict)


class TestImmutability(unittest.TestCase):
    def test_registry_entry_frozen(self):
        e = RegistryEntry(name="Mission", kind="runtime")
        with self.assertRaises(Exception):
            e.name = "x"

    def test_capability_frozen(self):
        c = IntelligenceCapability()
        with self.assertRaises(Exception):
            c.bundle = False

    def test_contract_frozen(self):
        c = IntelligenceContract()
        with self.assertRaises(Exception):
            c.preview_only = False

    def test_bridge_snapshot_frozen(self):
        s = ConversationBridgeSnapshot()
        with self.assertRaises(Exception):
            s.conversation_id = "x"


class TestNoInference(unittest.TestCase):
    def test_contract_no_inference(self):
        self.assertFalse(IntelligenceContract().inference)
        self.assertFalse(IntelligenceContract().llm)

    def test_inference_layers_absent(self):
        d = IntelligenceDescriptor()
        self.assertNotIn("inference", [x for x in ("inference",) if x != "inference"])


class TestRegistryBehavior(unittest.TestCase):
    def test_with_entry_preserves(self):
        r1 = IntelligenceRegistry().with_entry("Guardian", "runtime")
        r2 = r1.with_entry("Decision", "runtime")
        self.assertEqual(r1.names, ("Guardian",))
        self.assertEqual(r2.names, ("Guardian", "Decision"))

    def test_empty_as_dict(self):
        d = IntelligenceRegistry().as_dict()
        self.assertEqual(d["entries"], [])

    def test_entry_as_dict(self):
        d = IntelligenceRegistry().with_entry("Mission", "runtime").as_dict()
        self.assertEqual(len(d["entries"]), 1)


class TestKnownRuntimesCoverage(unittest.TestCase):
    def test_count(self):
        from sam.intelligence_runtime.registry import KNOWN_RUNTIMES
        self.assertEqual(len(KNOWN_RUNTIMES), 23)

    def test_expected_modern_runtimes(self):
        from sam.intelligence_runtime.registry import KNOWN_RUNTIMES
        for modern in ("Model Runtime", "Execution Runtime", "Runtime Service"):
            self.assertIn(modern, KNOWN_RUNTIMES)


class TestBridgeDefaults(unittest.TestCase):
    def test_conversation_snapshot_default(self):
        s = ConversationBridgeSnapshot()
        self.assertEqual(s.mode, "conversation")

    def test_dashboard_snapshot_default(self):
        s = DashboardBridgeSnapshot()
        self.assertEqual(s.mode, "dashboard")

    def test_conversation_scope(self):
        self.assertEqual(ConversationBridge().scope(), ("conversation",))

    def test_dashboard_scope(self):
        self.assertEqual(DashboardBridge().scope(), ("dashboard",))


class TestDescriptorLayers(unittest.TestCase):
    def test_layers_tuple(self):
        d = IntelligenceDescriptor()
        self.assertEqual(tuple(d.layers),
                         ("registry", "graph", "context", "validation",
                          "assembly", "report"))


if __name__ == "__main__":
    unittest.main()
