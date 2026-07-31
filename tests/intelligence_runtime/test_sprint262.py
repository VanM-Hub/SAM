"""Sprint 262 - Runtime Registry test."""
import unittest

from sam.intelligence_runtime.runtime_catalog import RuntimeCatalog
from sam.intelligence_runtime.runtime_descriptor import RuntimeDescriptor
from sam.intelligence_runtime.runtime_reference import RuntimeReference
from sam.intelligence_runtime.runtime_registry import RuntimeRegistry
from sam.intelligence_runtime.runtime_summary import RuntimeSummary


def make_ref(name, role="layer"):
    return RuntimeReference(
        descriptor=RuntimeDescriptor(name=name, kind="runtime"),
        role=role,
    )


RUNTIME_NAMES = (
    "Guardian", "Decision", "Approval", "Operational", "Activation",
    "Execution", "Runtime Kernel", "Connector", "Orchestrator", "Mission",
    "Provider", "Agent", "Skills", "Memory", "Knowledge", "Cognitive",
    "Workflow", "Policy", "Audit", "Artifact", "Model Runtime",
    "Execution Runtime", "Runtime Service",
)


class TestRuntimeDescriptor(unittest.TestCase):
    def test_immutable(self):
        d = RuntimeDescriptor(name="Mission", kind="runtime")
        with self.assertRaises(Exception):
            d.name = "x"


class TestRuntimeReference(unittest.TestCase):
    def test_reference_dict(self):
        r = make_ref("Mission")
        self.assertEqual(r.descriptor.name, "Mission")
        self.assertIn("descriptor", r.as_dict())


class TestRuntimeRegistry(unittest.TestCase):
    def test_register(self):
        reg = RuntimeRegistry().register(make_ref("Mission"))
        self.assertEqual(len(reg), 1)
        self.assertIn("Mission", reg.names())

    def test_register_many(self):
        reg = RuntimeRegistry().register_many(make_ref(n) for n in RUNTIME_NAMES)
        self.assertEqual(len(reg), len(RUNTIME_NAMES))
        # urutan terurut abjad
        names = reg.names()
        self.assertEqual(names, tuple(sorted(RUNTIME_NAMES, key=str.lower)))

    def test_no_provider_hardcode(self):
        providers = ("openai", "anthropic", "gemini", "deepseek",
                     "ollama", "openrouter")
        reg = RuntimeRegistry().register_many(make_ref(n) for n in RUNTIME_NAMES)
        for n in reg.names():
            self.assertNotIn(n.lower(), providers)

    def test_immutable_register(self):
        reg = RuntimeRegistry().register(make_ref("Mission"))
        first = reg.names()
        _ = reg.register(make_ref("Agent"))
        self.assertEqual(reg.names(), first)  # yang asli tidak berubah


class TestRuntimeCatalog(unittest.TestCase):
    def test_catalog(self):
        c = RuntimeCatalog(names=RUNTIME_NAMES)
        self.assertTrue(c.has("Guardian"))
        self.assertTrue(c.has("Runtime Service"))
        self.assertFalse(c.has("OpenAI"))
        self.assertEqual(len(c), len(RUNTIME_NAMES))


class TestRuntimeSummary(unittest.TestCase):
    def test_summary(self):
        reg = RuntimeRegistry().register_many(make_ref(n) for n in RUNTIME_NAMES)
        s = RuntimeSummary(registry=reg)
        self.assertEqual(s.total, len(RUNTIME_NAMES))
        self.assertIn("Runtime Service", s.layer_names())
        self.assertEqual(s.as_dict()["total"], len(RUNTIME_NAMES))


if __name__ == "__main__":
    unittest.main()
