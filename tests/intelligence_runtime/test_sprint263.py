"""Sprint 263 - Pipeline Graph test."""
import unittest

from sam.intelligence_runtime.pipeline_builder import PipelineBuilder
from sam.intelligence_runtime.pipeline_edge import PipelineEdge
from sam.intelligence_runtime.pipeline_graph import PipelineGraph
from sam.intelligence_runtime.pipeline_node import PipelineNode
from sam.intelligence_runtime.pipeline_validator import PipelineValidator


FINAL_PIPELINE = (
    "Mission", "Agent", "Workflow", "Skill", "Memory", "Knowledge",
    "Cognitive", "Policy", "Audit", "Artifact", "Intelligence Runtime",
    "Orchestrator", "Connector", "Provider", "Model Runtime",
    "Execution Runtime", "Runtime Service",
)


class TestPipelineNode(unittest.TestCase):
    def test_node_immutable(self):
        n = PipelineNode(name="Mission")
        with self.assertRaises(Exception):
            n.name = "x"
        self.assertEqual(n.kind, "stage")


class TestPipelineEdge(unittest.TestCase):
    def test_edge(self):
        e = PipelineEdge(source="Mission", target="Agent")
        self.assertEqual(e.target, "Agent")


class TestPipelineGraph(unittest.TestCase):
    def test_with_node_edge(self):
        g = PipelineGraph().with_node(PipelineNode("A")).with_node(PipelineNode("B"))
        g = g.with_edge(PipelineEdge("A", "B"))
        self.assertEqual(g.node_names(), ["A", "B"])
        self.assertEqual(g.adjacency(), {"A": ["B"]})

    def test_graph_immutable(self):
        g = PipelineGraph().with_node(PipelineNode("A"))
        g2 = g.with_node(PipelineNode("B"))
        self.assertEqual(g.node_names(), ["A"])  # asli tak berubah


class TestPipelineBuilder(unittest.TestCase):
    def test_build_final(self):
        g = PipelineBuilder.build(FINAL_PIPELINE)
        self.assertEqual(len(g.nodes), len(FINAL_PIPELINE))
        self.assertEqual(len(g.edges), len(FINAL_PIPELINE) - 1)
        self.assertEqual(g.node_names(), list(FINAL_PIPELINE))

    def test_build_not_execute(self):
        # builder hanya menyusun node/edge, tidak menjalankan apa pun
        g = PipelineBuilder.build(FINAL_PIPELINE[:-1])
        self.assertNotIn("Runtime Service", g.node_names())


class TestPipelineValidator(unittest.TestCase):
    def setUp(self):
        self.v = PipelineValidator()

    def test_valid_dag(self):
        g = PipelineBuilder.build(FINAL_PIPELINE)
        self.assertTrue(self.v.is_valid(g))

    def test_duplicate_node(self):
        g = (PipelineGraph()
             .with_node(PipelineNode("A")).with_node(PipelineNode("A")))
        issues = self.v.validate(g)
        self.assertTrue(any(i.code == "DUP_NODE" for i in issues))

    def test_missing_source(self):
        g = (PipelineGraph()
             .with_node(PipelineNode("A"))
             .with_edge(PipelineEdge("Missing", "A")))
        issues = self.v.validate(g)
        self.assertTrue(any(i.code == "MISSING_SOURCE" for i in issues))

    def test_cycle_detected(self):
        g = (PipelineGraph()
             .with_node(PipelineNode("A")).with_node(PipelineNode("B"))
             .with_edge(PipelineEdge("A", "B"))
             .with_edge(PipelineEdge("B", "A")))
        self.assertFalse(self.v.is_valid(g))
        self.assertTrue(any(i.code == "CYCLE" for i in self.v.validate(g)))

    def test_single_node_valid(self):
        g = PipelineGraph().with_node(PipelineNode("A"))
        self.assertTrue(self.v.is_valid(g))


if __name__ == "__main__":
    unittest.main()
