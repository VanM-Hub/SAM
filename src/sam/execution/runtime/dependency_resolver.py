"""Dependency Resolver, Validator, and Order Engine."""
from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.dependency_graph import (
    DependencyGraph, DependencyNode, DependencyValidation,
    ExecutionOrder, DependencySummary,
)


class DependencyGraphBuilder:
    """Builder untuk DependencyGraph dari daftar kandidat."""

    def build(self, candidates: List[ExecutionCandidate]) -> DependencyGraph:
        """Bangun dependency graph dari kandidat."""
        nodes: Dict[str, DependencyNode] = {}
        edges = 0
        levels = 0

        for c in candidates:
            deps = tuple(d for d in c.dependencies if d != c.candidate_id)
            if deps:
                edges += len(deps)
            nodes[c.candidate_id] = DependencyNode(
                candidate_id=c.candidate_id,
                depends_on=deps,
            )

        # Hitung level maksimum (depth)
        memo: Dict[str, int] = {}
        for cid in nodes:
            self._depth(cid, nodes, memo, set())
        levels = max(memo.values()) if memo else 0

        return DependencyGraph(nodes=nodes, edges=edges, levels=levels)

    def _depth(self, cid: str, nodes: Dict[str, DependencyNode],
               memo: Dict[str, int], visiting: Set[str]) -> int:
        """Hitung depth node secara rekursif."""
        if cid in memo:
            return memo[cid]
        if cid not in nodes:
            memo[cid] = 0
            return 0
        node = nodes[cid]
        if not node.depends_on:
            memo[cid] = 0
            return 0
        max_d = 0
        for dep_id in node.depends_on:
            dep_d = self._depth(dep_id, nodes, memo, visiting)
            max_d = max(max_d, dep_d + 1)
        memo[cid] = max_d
        return max_d


class DependencyValidator:
    """Validator dependensi — cek cycle dan missing deps."""

    def validate(self, graph: DependencyGraph,
                 candidates: List[ExecutionCandidate]) -> DependencyValidation:
        """Validasi dependensi."""
        errors: List[str] = []
        warnings: List[str] = []
        total = graph.edges

        candidate_ids = {c.candidate_id for c in candidates}

        # Cek missing dependency
        for cid, node in graph.nodes.items():
            for dep_id in node.depends_on:
                if dep_id not in candidate_ids:
                    errors.append(f"Missing dependency: {cid} -> {dep_id}")

        # Cek cycle (sederhana: jika A depends on B dan B depends on A)
        for cid, node in graph.nodes.items():
            for dep_id in node.depends_on:
                if dep_id in graph.nodes:
                    dep_node = graph.nodes[dep_id]
                    if cid in dep_node.depends_on:
                        warnings.append(f"Potential cycle: {cid} <-> {dep_id}")

        return DependencyValidation(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            total_dependencies=total,
        )


class ExecutionOrderResolver:
    """Resolver urutan eksekusi berdasarkan dependensi."""

    def resolve(self, graph: DependencyGraph,
                candidates: List[ExecutionCandidate]) -> ExecutionOrder:
        """Resolve urutan eksekusi (topological sort preview)."""
        candidate_ids = {c.candidate_id for c in candidates}
        order: list = []
        remaining = set(graph.nodes.keys()) & candidate_ids
        visited: Set[str] = set()
        has_cycles = False

        # Topological sort sederhana
        temp_mark: Set[str] = set()
        perm_mark: Set[str] = set()

        def visit(cid: str) -> bool:
            if cid in perm_mark:
                return True
            if cid in temp_mark:
                has_cycles_local = True
                return False
            if cid not in graph.nodes:
                return True
            temp_mark.add(cid)
            node = graph.nodes[cid]
            for dep_id in node.depends_on:
                if dep_id in candidate_ids:
                    visit(dep_id)
            temp_mark.discard(cid)
            perm_mark.add(cid)
            if cid not in order:
                order.append(cid)
            return True

        for cid in remaining:
            visit(cid)

        # Nodes tanpa dependensi juga dimasukkan
        for c in candidates:
            if c.candidate_id not in order:
                order.append(c.candidate_id)

        # Level-based grouping
        levels: List[Tuple[str, ...]] = []
        assigned: Set[str] = set()
        remaining_order = list(order)
        while remaining_order:
            level = []
            new_remaining = []
            for cid in remaining_order:
                if cid not in graph.nodes:
                    level.append(cid)
                    assigned.add(cid)
                else:
                    node = graph.nodes[cid]
                    if all(d in assigned or d not in candidate_ids for d in node.depends_on):
                        level.append(cid)
                        assigned.add(cid)
                    else:
                        new_remaining.append(cid)
            if not level:
                # Cycle — add remaining
                level = new_remaining
                remaining_order = []
                has_cycles = True
            else:
                levels.append(tuple(level))
                remaining_order = new_remaining

        return ExecutionOrder(
            order_id="order_1",
            ordered_candidate_ids=tuple(order),
            levels=levels,
            total_levels=len(levels),
            has_cycles=has_cycles,
        )

    def get_summary(self, graph: DependencyGraph,
                    order: ExecutionOrder) -> DependencySummary:
        """Buat ringkasan dependensi."""
        return DependencySummary(
            total_nodes=len(graph.nodes),
            total_edges=graph.edges,
            max_depth=graph.levels,
            has_cycles=order.has_cycles,
            status="verified" if not order.has_cycles else "has_cycles",
        )
