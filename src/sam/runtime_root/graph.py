"""Dependency graph for the Reference Runtime composition (E1-001).

Encodes the canonical linear chain from R5-001 / I1-001:

    CitizenHost -> CapabilityManager -> DiscoveryResolver
        -> ContractEnforcer -> ApprovalCoordinator
        -> ExecutionScheduler -> AuditRecorder

The graph must be acyclic and match this architecture. The composition layer
uses it to (a) validate the built graph and (b) derive wiring order.

Authority: E1-001 | R5-001 S2 | I1-001 Section 3 | I0-001 M2
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Optional, Tuple

from .exceptions import DependencyGraphError

#: Canonical unit identities in chain order.
UNIT_CHAIN = (
    "citizen_host",
    "capability_manager",
    "discovery_resolver",
    "contract_enforcer",
    "approval_coordinator",
    "execution_scheduler",
    "audit_recorder",
)

#: Edge source -> downstream dependency (the next unit in the chain).
CANONICAL_EDGES: Tuple[Tuple[str, str], ...] = (
    ("citizen_host", "capability_manager"),
    ("capability_manager", "discovery_resolver"),
    ("discovery_resolver", "contract_enforcer"),
    ("contract_enforcer", "approval_coordinator"),
    ("approval_coordinator", "execution_scheduler"),
    ("execution_scheduler", "audit_recorder"),
)


class DependencyGraph:
    """Immutable, validated graph of runtime unit dependencies.

    Building a graph performs a full acyclicity check and verifies every edge
    follows the canonical architecture chain.
    """

    def __init__(
        self,
        adjacency: Optional[
            Dict[str, FrozenSet[str]]
        ] = None,
        edges: Optional[List[Tuple[str, str]]] = None,
    ) -> None:
        self._adjacency: Dict[str, FrozenSet[str]] = {}
        if adjacency is not None:
            for node, deps in adjacency.items():
                self._adjacency[node] = frozenset(deps)
        if edges is not None:
            for src, dst in edges:
                cur = set(self._adjacency.get(src, frozenset()))
                cur.add(dst)
                self._adjacency[src] = frozenset(cur)
        self._validate()

    # -- construction ----------------------------------------------------

    @classmethod
    def canonical(cls) -> "DependencyGraph":
        """Build the canonical linear chain graph."""
        adj: Dict[str, FrozenSet[str]] = {}
        for src, dst in CANONICAL_EDGES:
            cur = set(adj.get(src, frozenset()))
            cur.add(dst)
            adj[src] = frozenset(cur)
        return cls(adjacency=adj)

    # -- validation ------------------------------------------------------

    def _validate(self) -> None:
        cycles = self.find_cycles()
        if cycles:
            raise DependencyGraphError(
                "Dependency graph contains cycle: %s" % (cycles,)
            )
        # Every declared edge must follow the canonical chain order.
        for src, deps in self._adjacency.items():
            for dst in deps:
                if not self._is_canonical_edge(src, dst):
                    raise DependencyGraphError(
                        "Edge %s -> %s violates canonical architecture chain"
                        % (src, dst)
                    )

    @staticmethod
    def _is_canonical_edge(src: str, dst: str) -> bool:
        """True iff src -> dst is an adjacent downstream link in the chain."""
        try:
            idx = UNIT_CHAIN.index(src)
        except ValueError:
            return False
        if idx + 1 >= len(UNIT_CHAIN):
            return False
        return UNIT_CHAIN[idx + 1] == dst

    def find_cycles(self) -> List[List[str]]:
        """Return all elementary cycles detected (empty list = acyclic)."""
        cycles: List[List[str]] = []
        visited: set = set()
        rec_stack: set = set()

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for nxt in sorted(self._adjacency.get(node, frozenset())):
                if nxt in rec_stack:
                    start = path.index(nxt)
                    cycles.append(path[start:] + [nxt])
                elif nxt not in visited:
                    dfs(nxt, path)
            rec_stack.discard(node)
            path.pop()

        for node in sorted(self._adjacency):
            if node not in visited:
                dfs(node, [])
        return cycles

    # -- accessors -------------------------------------------------------

    @property
    def nodes(self) -> FrozenSet[str]:
        """All nodes in the graph (sources and targets)."""
        nodes = set(self._adjacency.keys())
        for deps in self._adjacency.values():
            nodes.update(deps)
        return frozenset(nodes)

    def edges(self) -> List[Tuple[str, str]]:
        """All directed edges (stable order)."""
        result: List[Tuple[str, str]] = []
        for src in sorted(self._adjacency):
            for dst in sorted(self._adjacency[src]):
                result.append((src, dst))
        return result

    def is_acyclic(self) -> bool:
        """True iff the graph has no cycles."""
        return not self.find_cycles()

    def downstream(self, node: str) -> FrozenSet[str]:
        """Units that `node` points to (immediate dependencies)."""
        return self._adjacency.get(node, frozenset())

    def equals(self, other: "DependencyGraph") -> bool:
        """Structural equality (same node set and edges)."""
        return (
            self.nodes == other.nodes
            and set(self.edges()) == set(other.edges())
        )
