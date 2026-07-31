"""Sprint 262 - Runtime Registry: test lanjutan."""
import unittest

from sam.intelligence_runtime.runtime_catalog import RuntimeCatalog
from sam.intelligence_runtime.runtime_descriptor import RuntimeDescriptor
from sam.intelligence_runtime.runtime_reference import RuntimeReference
from sam.intelligence_runtime.runtime_registry import RuntimeRegistry
from sam.intelligence_runtime.runtime_summary import RuntimeSummary


RUNTIME_NAMES = (
    "Guardian", "Decision", "Approval", "Operational", "Activation",
    "Execution", "Runtime Kernel", "Connector", "Orchestrator", "Mission",
    "Provider", "Agent", "Skills", "Memory", "Knowledge", "Cognitive",
    "Workflow", "Policy", "Audit", "Artifact", "Model Runtime",
    "Execution Runtime", "Runtime Service",
)


def ref(name, role="layer"):
    return RuntimeReference(
        descriptor=RuntimeDescriptor(name=name, kind="runtime"), role=role)


class TestRuntimeDescriptorBehavior(unittest.TestCase):
    def test_default_version(self):
        self.assertEqual(RuntimeDescriptor(name="X", kind="y").version, "28.0.0")

    def test_as_dict_fields(self):
        d = RuntimeDescriptor(name="Mission", kind="runtime").as_dict()
        self.assertEqual(d["name"], "Mission")
        self.assertIn("version", d)


class TestRuntimeReferenceBehavior(unittest.TestCase):
    def test_aliases_empty_default(self):
        self.assertEqual(ref("Mission").aliases, ())

    def test_role(self):
        self.assertEqual(ref("Activation", role="runtime").role, "runtime")

    def test_as_dict_aliases(self):
        r = RuntimeReference(
            descriptor=RuntimeDescriptor(name="Agent", kind="x"),
            aliases=("agent",))
        self.assertEqual(r.as_dict()["aliases"], ["agent"])


class TestRuntimeRegistryBehavior(unittest.TestCase):
    def test_sorted_names(self):
        reg = RuntimeRegistry().register_many(ref(n) for n in RUNTIME_NAMES)
        names = reg.names()
        self.assertEqual(names, tuple(sorted(RUNTIME_NAMES, key=str.lower)))

    def test_refs_count(self):
        reg = RuntimeRegistry().register(ref("Mission"))
        self.assertEqual(len(reg.refs), 1)

    def test_many_chain(self):
        reg = RuntimeRegistry()
        for n in RUNTIME_NAMES:
            reg = reg.register(ref(n))
        self.assertEqual(len(reg), len(RUNTIME_NAMES))

    def test_as_dict_count(self):
        reg = RuntimeRegistry().register_many(ref(n) for n in RUNTIME_NAMES)
        d = reg.as_dict()
        self.assertEqual(d["count"], len(RUNTIME_NAMES))
        self.assertEqual(len(d["runtimes"]), len(RUNTIME_NAMES))

    def test_names_unique(self):
        reg = RuntimeRegistry().register_many([ref("Mission"), ref("Mission")])
        self.assertEqual(len(reg), 2)  # diizinkan, tidak digabung


class TestRuntimeCatalogBehavior(unittest.TestCase):
    def test_empty_catalog(self):
        c = RuntimeCatalog(names=())
        self.assertEqual(len(c), 0)
        self.assertFalse(c.has("anything"))

    def test_as_list(self):
        c = RuntimeCatalog(names=("A", "B"))
        self.assertEqual(c.as_list(), ("A", "B"))

    def test_has_case_sensitive(self):
        c = RuntimeCatalog(names=("Runtime Service",))
        self.assertFalse(c.has("runtime service"))


class TestRuntimeSummaryBehavior(unittest.TestCase):
    def test_empty_summary(self):
        s = RuntimeSummary(registry=RuntimeRegistry())
        self.assertEqual(s.total, 0)
        self.assertEqual(s.layer_names(), ())
        self.assertEqual(s.as_dict()["total"], 0)

    def test_layer_names_filled(self):
        reg = RuntimeRegistry().register_many(ref(n, "runtime") for n in RUNTIME_NAMES)
        s = RuntimeSummary(registry=reg)
        self.assertEqual(len(s.layer_names()), len(RUNTIME_NAMES))


if __name__ == "__main__":
    unittest.main()
