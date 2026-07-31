"""Sprint 263 - Pipeline Graph: pipeline_graph (grafik immutable, tidak menjalankan runtime)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .pipeline_edge import PipelineEdge
from .pipeline_node import PipelineNode


@dataclass(frozen=True)
class PipelineGraph:
    """Graf pipeline runtime: node + edge, deterministik, preview-only."""

    _nodes: Tuple[PipelineNode, ...] = ()
    _edges: Tuple[PipelineEdge, ...] = ()

    def with_node(self, node: PipelineNode) -> "PipelineGraph":
        return PipelineGraph(_nodes=self._nodes + (node,), _edges=self._edges)

    def with_edge(self, edge: PipelineEdge) -> "PipelineGraph":
        return PipelineGraph(_nodes=self._nodes, _edges=self._edges + (edge,))

    @property
    def nodes(self) -> Tuple[PipelineNode, ...]:
        return self._nodes

    @property
    def edges(self) -> Tuple[PipelineEdge, ...]:
        return self._edges

    def node_names(self) -> List[str]:
        return [n.name for n in self._nodes]

    def adjacency(self) -> Dict[str, List[str]]:
        adj: Dict[str, List[str]] = {}
        for e in self._edges:
            adj.setdefault(e.source, []).append(e.target)
        return adj

    def as_dict(self) -> dict:
        return {
            "nodes": [n.as_dict() for n in self._nodes],
            "edges": [e.as_dict() for e in self._edges],
        }
