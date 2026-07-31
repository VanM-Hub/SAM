"""Sprint 263 - Pipeline Graph: pipeline_validator.

Memvalidasi graph secara statis: node unik, edge merujuk node ada,
tidak ada cycle (DAG). Tidak menjalankan runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .pipeline_graph import PipelineGraph


@dataclass(frozen=True)
class ValidationIssue:
    """Isu validasi (path, kode, pesan)."""

    path: str
    code: str
    message: str


@dataclass(frozen=True)
class PipelineValidator:
    """Validator DAG untuk pipeline graph."""

    def validate(self, graph: PipelineGraph) -> Tuple[ValidationIssue, ...]:
        issues: List[ValidationIssue] = []

        # node unik
        names = graph.node_names()
        dupes = {n for n in names if names.count(n) > 1}
        for d in dupes:
            issues.append(ValidationIssue(
                path=f"node:{d}", code="DUP_NODE",
                message=f"Node duplikat: {d}"))

        node_set = set(names)
        for e in graph.edges:
            if e.source not in node_set:
                issues.append(ValidationIssue(
                    path=f"edge:{e.source}->{e.target}", code="MISSING_SOURCE",
                    message=f"Source edge tidak ada: {e.source}"))
            if e.target not in node_set:
                issues.append(ValidationIssue(
                    path=f"edge:{e.source}->{e.target}", code="MISSING_TARGET",
                    message=f"Target edge tidak ada: {e.target}"))

        # Cek cycle (DFS) -> DAG wajib
        if self._has_cycle(graph):
            issues.append(ValidationIssue(
                path="graph", code="CYCLE",
                message="Graph mengandung cycle; pipeline harus DAG"))

        return tuple(issues)

    def _has_cycle(self, graph: PipelineGraph) -> bool:
        adj = graph.adjacency()
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n: WHITE for n in graph.node_names()}

        def dfs(u: str) -> bool:
            color[u] = GRAY
            for v in adj.get(u, []):
                if color.get(v, WHITE) == GRAY:
                    return True
                if color.get(v, WHITE) == WHITE:
                    if dfs(v):
                        return True
            color[u] = BLACK
            return False

        for n in graph.node_names():
            if color[n] == WHITE:
                if dfs(n):
                    return True
        return False

    def is_valid(self, graph: PipelineGraph) -> bool:
        return len(self.validate(graph)) == 0
