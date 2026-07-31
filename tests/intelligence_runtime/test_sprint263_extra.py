"""Sprint 263 - Pipeline Graph: test lanjutan."""
import unittest

from sam.intelligence_runtime.pipeline_builder import PipelineBuilder
from sam.intelligence_runtime.pipeline_edge import PipelineEdge
from sam.intelligence_runtime.pipeline_graph import PipelineGraph
from sam.intelligence_runtime.pipeline_node import PipelineNode
from sam.intelligence_runtime.pipeline_validator import (
    PipelineValidator,
    ValidationIssue,
)


def chain(names):
    return PipelineBuilder.build(names)


class TestPipelineNodeBehavior(unittest.TestCase):
    def test_attributes_empty_default(self):
        self.assertEqual(PipelineNode("A").attributes, {})

    def test_attributes(self):
        n = PipelineNode("A", attributes={"weight": 1})
        self.assertEqual(n.attributes["weight"], 1)

    def test_kind(self):
        self.assertEqual(PipelineNode("A", kind="source").kind, "source")

    def test_node_as_dict(self):
        d = PipelineNode("A").as_dict()
        self.assertEqual(d["name"], "A")


class TestPipelineEdgeBehavior(unittest.TestCase):
    def test_kind_default(self):
        self.assertEqual(PipelineEdge("A", "B").kind, "flow")

    def test_as_dict(self):
        d = PipelineEdge("A", "B").as_dict()
        self.assertEqual(d["source"], "A")
        self.assertEqual(d["target"], "B")


class TestPipelineGraphBehavior(unittest.TestCase):
    def test_empty(self):
        g = PipelineGraph()
        self.assertEqual(g.node_names(), [])
        self.assertEqual(g.adjacency(), {})

    def test_multiple_edges(self):
        g = (PipelineGraph()
             .with_node(PipelineNode("A"))
             .with_node(PipelineNode("B"))
             .with_node(PipelineNode("C"))
             .with_edge(PipelineEdge("A", "B"))
             .with_edge(PipelineEdge("A", "C")))
        self.assertEqual(g.adjacency()["A"], ["B", "C"])

    def test_as_dict(self):
        g = PipelineGraph().with_node(PipelineNode("A"))
        d = g.as_dict()
        self.assertEqual(len(d["nodes"]), 1)
        self.assertEqual(d["edges"], [])


class TestPipelineValidatorBehavior(unittest.TestCase):
    def setUp(self):
        self.v = PipelineValidator()

    def test_validation_issue_frozen(self):
        i = ValidationIssue(path="a", code="B", message="m")
        with self.assertRaises(Exception):
            i.code = "C"

    def test_self_loop_is_cycle(self):
        g = (PipelineGraph()
             .with_node(PipelineNode("A"))
             .with_edge(PipelineEdge("A", "A")))
        self.assertFalse(self.v.is_valid(g))
        codes = [i.code for i in self.v.validate(g)]
        self.assertIn("CYCLE", codes)

    def test_valid_long_chain(self):
        g = chain(("A", "B", "C", "D", "E"))
        self.assertTrue(self.v.is_valid(g))

    def test_empty_graph_valid(self):
        g = PipelineGraph()
        self.assertTrue(self.v.is_valid(g))

    def test_two_cycles(self):
        g = (PipelineGraph()
             .with_node(PipelineNode("A")).with_node(PipelineNode("B"))
             .with_node(PipelineNode("C"))
             .with_edge(PipelineEdge("A", "B")).with_edge(PipelineEdge("B", "A"))
             .with_edge(PipelineEdge("B", "C")).with_edge(PipelineEdge("C", "B")))
        self.assertFalse(self.v.is_valid(g))


class TestPipelineBuilderBehavior(unittest.TestCase):
    def test_empty_build(self):
        g = PipelineBuilder.build([])
        self.assertEqual(g.node_names(), [])
        self.assertEqual(g.edges, ())

    def test_single_stage(self):
        g = PipelineBuilder.build(["Mission"])
        self.assertEqual(len(g.nodes), 1)
        self.assertEqual(len(g.edges), 0)

    def test_edges_connect_consecutive(self):
        g = chain(("A", "B", "C"))
        edges = g.edges
        self.assertEqual((edges[0].source, edges[0].target), ("A", "B"))
        self.assertEqual((edges[1].source, edges[1].target), ("B", "C"))


if __name__ == "__main__":
    unittest.main()
