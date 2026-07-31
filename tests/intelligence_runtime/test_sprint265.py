"""Sprint 265 - Intelligence Runtime test."""
import unittest

from sam.intelligence_runtime.intelligence_runtime import IntelligenceRuntime
from sam.intelligence_runtime.runtime_descriptor import RuntimeDescriptor
from sam.intelligence_runtime.runtime_pipeline import RuntimePipeline
from sam.intelligence_runtime.runtime_reference import RuntimeReference
from sam.intelligence_runtime.runtime_registry import RuntimeRegistry
from sam.intelligence_runtime.runtime_report import RuntimeReport
from sam.intelligence_runtime.runtime_session import RuntimeSession
from sam.intelligence_runtime.runtime_status import RuntimeStatus


def make_ref(name, role="layer"):
    return RuntimeReference(
        descriptor=RuntimeDescriptor(name=name, kind="runtime"), role=role)


RUNTIME_NAMES = (
    "Guardian", "Decision", "Approval", "Operational", "Activation",
    "Execution", "Runtime Kernel", "Connector", "Orchestrator", "Mission",
    "Provider", "Agent", "Skills", "Memory", "Knowledge", "Cognitive",
    "Workflow", "Policy", "Audit", "Artifact", "Model Runtime",
    "Execution Runtime", "Runtime Service",
)


def runtime_instance():
    reg = RuntimeRegistry().register_many(make_ref(n) for n in RUNTIME_NAMES)
    return IntelligenceRuntime(registry=reg)


class TestRuntimePipeline(unittest.TestCase):
    def test_stages(self):
        p = RuntimePipeline()
        self.assertEqual(list(p.stages), [
            "Registry", "Graph", "Context", "Validation", "Assembly", "Report"])
        self.assertEqual(p.index("Graph"), 1)


class TestRuntimeStatus(unittest.TestCase):
    def test_preview_mode(self):
        s = RuntimeStatus()
        self.assertEqual(s.mode, "preview")
        self.assertEqual(s.state, "ready")


class TestRuntimeReport(unittest.TestCase):
    def test_immutable(self):
        r = RuntimeReport(stages=("Registry",), artifacts={"a": 1})
        with self.assertRaises(Exception):
            r.stages = ()
        self.assertEqual(r.as_dict()["stages"], ["Registry"])


class TestRuntimeSession(unittest.TestCase):
    def test_session(self):
        s = RuntimeSession(completed=True)
        self.assertTrue(s.completed)
        self.assertIn("completed", s.as_dict())


class TestIntelligenceRuntime(unittest.TestCase):
    def test_run_produces_report(self):
        rt = runtime_instance()
        session = rt.run()
        self.assertTrue(session.completed)
        art = session.report.artifacts
        self.assertEqual(art["graph_valid"], True)
        node_names = [n["name"] for n in art["graph"]["nodes"]]
        self.assertIn("Runtime Service", node_names)

    def test_pipeline_stages_recorded(self):
        rt = runtime_instance()
        session = rt.run()
        self.assertEqual(list(session.report.stages), list(RuntimePipeline().stages))

    def test_no_inference_no_llm(self):
        rt = runtime_instance()
        d = rt.as_dict()
        self.assertFalse(d["inference"])
        self.assertFalse(d["llm"])
        self.assertTrue(d["preview_only"])

    def test_deterministic(self):
        rt = runtime_instance()
        a = rt.run().report.as_dict()
        b = rt.run().report.as_dict()
        self.assertEqual(a, b)

    def test_graph_is_dag(self):
        rt = runtime_instance()
        ses = rt.run()
        self.assertTrue(ses.report.artifacts["graph_valid"])

    def test_context_default_filled(self):
        rt = runtime_instance()
        ses = rt.run()
        ctx = ses.report.artifacts["context"]
        # ada section Mission..Execution dari default
        self.assertIn("Mission", ctx["sections"])
        self.assertIn("Execution", ctx["sections"])

    def test_does_not_execute_runtime(self):
        # run() hanya menyusun representasi, tidak memanggil eksekusi
        rt = runtime_instance()
        ses = rt.run()
        self.assertIn("graph", ses.report.artifacts)
        self.assertNotIn("executed", ses.report.artifacts)


if __name__ == "__main__":
    unittest.main()
