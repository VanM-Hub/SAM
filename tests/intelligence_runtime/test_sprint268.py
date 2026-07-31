"""Sprint 268 - Integration test."""
import unittest

from sam.intelligence_runtime import FINAL_PIPELINE, IntelligenceIntegration
from sam.intelligence_runtime.intelligence_pipeline import IntelligencePipeline
from sam.intelligence_runtime.intelligence_runtime import IntelligenceRuntime
from sam.intelligence_runtime.runtime_descriptor import RuntimeDescriptor
from sam.intelligence_runtime.runtime_reference import RuntimeReference
from sam.intelligence_runtime.runtime_registry import RuntimeRegistry


def make_ref(name, role="layer"):
    return RuntimeReference(
        descriptor=RuntimeDescriptor(name=name, kind="runtime"), role=role)


REGISTRY_NAMES = (
    "Guardian", "Decision", "Approval", "Operational", "Activation",
    "Execution", "Runtime Kernel", "Connector", "Orchestrator", "Mission",
    "Provider", "Agent", "Skills", "Memory", "Knowledge", "Cognitive",
    "Workflow", "Policy", "Audit", "Artifact", "Model Runtime",
    "Execution Runtime", "Runtime Service",
)


def runtime():
    reg = RuntimeRegistry().register_many(make_ref(n) for n in REGISTRY_NAMES)
    return IntelligenceRuntime(registry=reg)


class TestIntelligencePipeline(unittest.TestCase):
    def test_final_pipeline(self):
        p = IntelligencePipeline()
        self.assertEqual(list(p.stages), list(FINAL_PIPELINE))
        self.assertEqual(len(p), 17)

    def test_intelligence_position(self):
        p = IntelligencePipeline()
        self.assertEqual(p.index("Artifact"), 9)
        self.assertEqual(p.index("Intelligence Runtime"), 10)
        self.assertEqual(p.index("Orchestrator"), 11)

    def test_pipeline_descends(self):
        # Mission pertama, Runtime Service terakhir
        self.assertEqual(FINAL_PIPELINE[0], "Mission")
        self.assertEqual(FINAL_PIPELINE[-1], "Runtime Service")


class TestIntelligenceIntegration(unittest.TestCase):
    def test_integration_readonly(self):
        rt = runtime()
        integ = IntelligenceIntegration()
        session = integ.run(rt)
        self.assertTrue(session.completed)

    def test_integration_pipeline_summary(self):
        integ = IntelligenceIntegration()
        self.assertEqual(integ.pipeline_summary(), FINAL_PIPELINE)

    def test_integration_no_execution(self):
        rt = runtime()
        session = IntelligenceIntegration().run(rt)
        art = session.report.artifacts
        self.assertIn("graph", art)
        self.assertNotIn("executed", art)

    def test_integration_deterministic(self):
        rt = runtime()
        a = IntelligenceIntegration().run(rt).report.as_dict()
        b = IntelligenceIntegration().run(rt).report.as_dict()
        self.assertEqual(a, b)


class TestEndToEnd(unittest.TestCase):
    def test_full_flow(self):
        rt = runtime()
        session = rt.run()
        self.assertTrue(session.completed)
        art = session.report.artifacts
        # context punya section inti
        ctx = art["context"]
        for s in ("Mission", "Agent", "Workflow", "Skill", "Memory",
                  "Knowledge", "Policy", "Audit", "Artifact",
                  "Model", "Provider", "Execution"):
            self.assertIn(s, ctx["sections"])
        # graph valid
        self.assertTrue(art["graph_valid"])


if __name__ == "__main__":
    unittest.main()
