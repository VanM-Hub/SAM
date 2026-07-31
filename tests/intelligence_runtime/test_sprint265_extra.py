"""Sprint 265 - Intelligence Runtime: test lanjutan."""
import unittest

from sam.intelligence_runtime.context_builder import ContextBuilder
from sam.intelligence_runtime.context_validator import ContextValidator
from sam.intelligence_runtime.intelligence_runtime import IntelligenceRuntime
from sam.intelligence_runtime.runtime_descriptor import RuntimeDescriptor
from sam.intelligence_runtime.runtime_reference import RuntimeReference
from sam.intelligence_runtime.runtime_registry import RuntimeRegistry


def ref(name, role="layer"):
    return RuntimeReference(
        descriptor=RuntimeDescriptor(name=name, kind="runtime"), role=role)


NAMES = ("Mission", "Agent", "Workflow", "Skill", "Memory", "Knowledge",
         "Cognitive", "Policy", "Audit", "Artifact", "Orchestrator",
         "Connector", "Provider")


def rt():
    reg = RuntimeRegistry().register_many(ref(n) for n in NAMES)
    return IntelligenceRuntime(registry=reg)


class TestRegistryArtifact(unittest.TestCase):
    def test_registry_artifact_count(self):
        ses = rt().run()
        reg = ses.report.artifacts["registry"]
        self.assertEqual(reg["count"], len(NAMES))

    def test_registry_artifact_names(self):
        ses = rt().run()
        reg = ses.report.artifacts["registry"]
        runtimes = [r["descriptor"]["name"] for r in reg["runtimes"]]
        for n in NAMES:
            self.assertIn(n, runtimes)


class TestGraphArtifact(unittest.TestCase):
    def test_graph_valid(self):
        ses = rt().run()
        self.assertTrue(ses.report.artifacts["graph_valid"])

    def test_graph_nodes_match_registry(self):
        ses = rt().run()
        nodes = [n["name"] for n in ses.report.artifacts["graph"]["nodes"]]
        self.assertEqual(set(nodes), set(NAMES))


class TestContextIntegration(unittest.TestCase):
    def test_context_has_all_required(self):
        ses = rt().run()
        ctx = ses.report.artifacts["context"]
        for s in ("Mission", "Agent", "Workflow", "Skill", "Memory",
                  "Knowledge", "Policy", "Audit", "Artifact",
                  "Model", "Provider", "Execution"):
            self.assertIn(s, ctx["sections"])

    def test_custom_context_builder(self):
        b = ContextBuilder.create()
        b = b.add("Mission", {"custom": 1})
        ses = rt().run(context_builder=b)
        ctx = ses.report.artifacts["context"]
        # hanya Mission yang ada -> tidak complete
        self.assertFalse(ses.completed)
        self.assertIn("Mission", ctx["sections"])


class TestDeterminism(unittest.TestCase):
    def test_repeated_runs_identical(self):
        inst = rt()
        results = [inst.run().report.as_dict() for _ in range(3)]
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])


class TestPurity(unittest.TestCase):
    def test_artifacts_no_execution_key(self):
        ses = rt().run()
        self.assertNotIn("executed", ses.report.artifacts)

    def test_session_completed_true_full(self):
        ses = rt().run()
        self.assertTrue(ses.completed)


if __name__ == "__main__":
    unittest.main()
