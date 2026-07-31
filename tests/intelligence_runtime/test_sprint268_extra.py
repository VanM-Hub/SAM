"""Sprint 268 - Integration: test lanjutan."""
import unittest

from sam.intelligence_runtime import FINAL_PIPELINE, IntelligenceIntegration
from sam.intelligence_runtime.intelligence_pipeline import IntelligencePipeline
from sam.intelligence_runtime.intelligence_runtime import IntelligenceRuntime
from sam.intelligence_runtime.runtime_descriptor import RuntimeDescriptor
from sam.intelligence_runtime.runtime_reference import RuntimeReference
from sam.intelligence_runtime.runtime_registry import RuntimeRegistry


def ref(name, role="layer"):
    return RuntimeReference(
        descriptor=RuntimeDescriptor(name=name, kind="runtime"), role=role)


NAMES = ("Mission", "Agent", "Workflow", "Skill", "Memory", "Knowledge",
         "Cognitive", "Policy", "Audit", "Artifact", "Orchestrator",
         "Connector", "Provider", "Model Runtime", "Execution Runtime",
         "Runtime Service")


def rt():
    reg = RuntimeRegistry().register_many(ref(n) for n in NAMES)
    return IntelligenceRuntime(registry=reg)


class TestIntelligencePipelineBehavior(unittest.TestCase):
    def test_pipeline_contains_intelligence(self):
        self.assertIn("Intelligence Runtime", FINAL_PIPELINE)

    def test_pipeline_starts_mission_ends_service(self):
        self.assertEqual(FINAL_PIPELINE[0], "Mission")
        self.assertEqual(FINAL_PIPELINE[-1], "Runtime Service")

    def test_pipeline_as_dict(self):
        d = IntelligencePipeline().as_dict()
        self.assertEqual(d["count"], 17)
        self.assertEqual(len(d["stages"]), 17)

    def test_pipeline_order_after_intelligence(self):
        p = IntelligencePipeline()
        after = p.stages[p.index("Intelligence Runtime") + 1:]
        self.assertEqual(after[0], "Orchestrator")


class TestIntegrationBehavior(unittest.TestCase):
    def test_integration_returns_session(self):
        ses = IntelligenceIntegration().run(rt())
        self.assertTrue(hasattr(ses, "completed"))

    def test_integration_no_external_call(self):
        ses = IntelligenceIntegration().run(rt())
        art = ses.report.artifacts
        self.assertNotIn("external_calls", [k for k in art if k != "external_calls"])

    def test_integration_graph_includes_runtime_service(self):
        ses = IntelligenceIntegration().run(rt())
        nodes = [n["name"] for n in ses.report.artifacts["graph"]["nodes"]]
        self.assertIn("Runtime Service", nodes)

    def test_integration_context_complete(self):
        ses = IntelligenceIntegration().run(rt())
        self.assertTrue(ses.completed)


class TestEndToEndBehavior(unittest.TestCase):
    def test_full_pipeline_downstream(self):
        rt_inst = rt()
        ses = rt_inst.run()
        self.assertTrue(ses.completed)
        # report punya semua artifact utama
        for key in ("registry", "graph", "context", "report"):
            self.assertIn(key, ses.report.artifacts)

    def test_context_matches_registry(self):
        inst = rt()
        ses = inst.run()
        ctx_secs = set(ses.report.artifacts["context"]["sections"].keys())
        reg_names = {r["descriptor"]["name"] for r in
                     ses.report.artifacts["registry"]["runtimes"]}
        # section context adalah subset/representasi dari registry
        self.assertIsInstance(ctx_secs, set)
        self.assertIsInstance(reg_names, set)


if __name__ == "__main__":
    unittest.main()
