"""Sprint 263 - Pipeline Graph: pipeline_builder (membangun graph dari daftar tahap)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .pipeline_edge import PipelineEdge
from .pipeline_graph import PipelineGraph
from .pipeline_node import PipelineNode


@dataclass(frozen=True)
class PipelineBuilder:
    """Builder deterministik: urutan nama tahap -> graph ber-urutan."""

    @staticmethod
    def build(stages: Sequence[str]) -> PipelineGraph:
        graph = PipelineGraph()
        for s in stages:
            graph = graph.with_node(PipelineNode(name=s, kind="stage"))
        for i in range(len(stages) - 1):
            graph = graph.with_edge(PipelineEdge(source=stages[i], target=stages[i + 1]))
        return graph
