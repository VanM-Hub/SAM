"""
OP-271 — Mission Dependency Graph

Directed Acyclic Graph (DAG) untuk proposal operasional.
Node: Proposal | Mission | Approval | Resource
Edge: depends_on | blocks | requires | follows

Fitur:
  - Dependency lookup
  - Root detection (nodes with no inbound edges)
  - Leaf detection (nodes with no outbound edges)
  - Cycle validation
  - Execution ordering (topological sort)

Constraints:
  - 0 domain changes
  - 0 repository changes
  - Read-only terhadap domain
  - Output berupa DTO
  - Tidak mengubah MissionController
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeKind(Enum):
    PROPOSAL = "proposal"
    MISSION = "mission"
    APPROVAL = "approval"
    RESOURCE = "resource"


class EdgeKind(Enum):
    DEPENDS_ON = "depends_on"
    BLOCKS = "blocks"
    REQUIRES = "requires"
    FOLLOWS = "follows"


@dataclass(frozen=True)
class GraphNode:
    id: str
    kind: NodeKind
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    kind: EdgeKind
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DependencyGraphDTO:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    roots: tuple[str, ...] = ()
    leaves: tuple[str, ...] = ()
    has_cycle: bool = False
    cycle_path: tuple[str, ...] = ()
    execution_order: tuple[str, ...] = ()
    node_count: int = 0
    edge_count: int = 0


class CycleError(Exception):
    """Raised when a cycle is detected during topological sort."""


class MissionDependencyGraph:
    """
    Directed Acyclic Graph untuk proposal operasional.

    Menyimpan node dan edge, menyediakan query untuk dependency,
    root/leaf detection, cycle validation, dan execution ordering.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, list[GraphEdge]] = {}  # source -> edges
        self._inbound: dict[str, list[GraphEdge]] = {}  # target -> edges

    # ── Node Management ──────────────────────────────────────────────

    def add_node(self, node_id: str, kind: NodeKind, label: str = "",
                 metadata: dict[str, Any] | None = None) -> None:
        if node_id in self._nodes:
            return
        self._nodes[node_id] = GraphNode(
            id=node_id, kind=kind, label=label,
            metadata=metadata or {},
        )
        self._edges.setdefault(node_id, [])
        self._inbound.setdefault(node_id, [])

    def remove_node(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)
        # Remove all edges where this node participates
        for src in list(self._edges.keys()):
            self._edges[src] = [e for e in self._edges[src]
                                if e.source_id != node_id and e.target_id != node_id]
        for tgt in list(self._inbound.keys()):
            self._inbound[tgt] = [e for e in self._inbound[tgt]
                                  if e.source_id != node_id and e.target_id != node_id]
        self._edges.pop(node_id, None)
        self._inbound.pop(node_id, None)

    def get_node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    @property
    def nodes(self) -> dict[str, GraphNode]:
        return dict(self._nodes)

    # ── Edge Management ──────────────────────────────────────────────

    def add_edge(self, source_id: str, target_id: str,
                 kind: EdgeKind = EdgeKind.DEPENDS_ON,
                 metadata: dict[str, Any] | None = None) -> None:
        if source_id not in self._nodes:
            raise ValueError(f"Source node '{source_id}' not found")
        if target_id not in self._nodes:
            raise ValueError(f"Target node '{target_id}' not found")

        edge = GraphEdge(
            source_id=source_id, target_id=target_id,
            kind=kind, metadata=metadata or {},
        )
        self._edges[source_id].append(edge)
        self._inbound[target_id].append(edge)

    def remove_edge(self, source_id: str, target_id: str) -> None:
        self._edges[source_id] = [e for e in self._edges.get(source_id, [])
                                  if e.target_id != target_id]
        self._inbound[target_id] = [e for e in self._inbound.get(target_id, [])
                                    if e.source_id != source_id]

    def get_outbound(self, node_id: str) -> list[GraphEdge]:
        return list(self._edges.get(node_id, []))

    def get_inbound(self, node_id: str) -> list[GraphEdge]:
        return list(self._inbound.get(node_id, []))

    # ── Dependency Lookup ────────────────────────────────────────────

    def dependencies_of(self, node_id: str) -> list[GraphNode]:
        """Return nodes that this node depends on (inbound DEPENDS_ON/REQUIRES)."""
        result: list[GraphNode] = []
        for edge in self._inbound.get(node_id, []):
            if edge.kind in (EdgeKind.DEPENDS_ON, EdgeKind.REQUIRES):
                node = self._nodes.get(edge.source_id)
                if node:
                    result.append(node)
        return result

    def dependents_of(self, node_id: str) -> list[GraphNode]:
        """Return nodes that depend on this node (outbound DEPENDS_ON/REQUIRES)."""
        result: list[GraphNode] = []
        for edge in self._edges.get(node_id, []):
            if edge.kind in (EdgeKind.DEPENDS_ON, EdgeKind.REQUIRES):
                node = self._nodes.get(edge.target_id)
                if node:
                    result.append(node)
        return result

    def blocked_by(self, node_id: str) -> list[GraphNode]:
        """Return nodes that block this node (inbound BLOCKS)."""
        result: list[GraphNode] = []
        for edge in self._inbound.get(node_id, []):
            if edge.kind == EdgeKind.BLOCKS:
                node = self._nodes.get(edge.source_id)
                if node:
                    result.append(node)
        return result

    # ── Root & Leaf Detection ────────────────────────────────────────

    def find_roots(self) -> list[GraphNode]:
        """Nodes with no inbound edges = no dependencies."""
        return [n for n in self._nodes.values()
                if not self._inbound.get(n.id, [])]

    def find_leaves(self) -> list[GraphNode]:
        """Nodes with no outbound edges = no dependents."""
        return [n for n in self._nodes.values()
                if not self._edges.get(n.id, [])]

    # ── Cycle Validation ─────────────────────────────────────────────

    def _has_cycle_dfs(self) -> tuple[bool, list[str]]:
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {nid: WHITE for nid in self._nodes}
        parent: dict[str, str | None] = {}
        cycle_path: list[str] = []

        def dfs(u: str) -> bool:
            color[u] = GRAY
            for edge in self._edges.get(u, []):
                v = edge.target_id
                if v not in color:
                    continue
                if color[v] == GRAY:
                    # Cycle found — reconstruct path
                    cycle_path.clear()
                    cycle_path.append(v)
                    cur = u
                    while cur is not None and cur != v:
                        cycle_path.append(cur)
                        cur = parent.get(cur)
                    cycle_path.append(v)
                    cycle_path.reverse()
                    return True
                if color[v] == BLACK:
                    parent[v] = u
                    if dfs(v):
                        return True
            color[u] = BLACK
            return False

        for nid in self._nodes:
            if color[nid] == WHITE:
                parent[nid] = None
                if dfs(nid):
                    return True, list(cycle_path)
        return False, []

    def has_cycle(self) -> bool:
        return self._has_cycle_dfs()[0]

    def find_cycle(self) -> list[str]:
        return self._has_cycle_dfs()[1]

    # ── Topological Sort (Execution Ordering) ────────────────────────

    def execution_order(self) -> list[str]:
        """
        Return topological ordering.

        Raises CycleError if a cycle is detected.
        """
        has_cycle, path = self._has_cycle_dfs()
        if has_cycle:
            raise CycleError(f"Cycle detected: {' -> '.join(path)}")

        in_degree: dict[str, int] = {}
        for nid in self._nodes:
            in_degree[nid] = len(self._inbound.get(nid, []))

        # Kahn's algorithm
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        order: list[str] = []

        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for edge in self._edges.get(nid, []):
                tid = edge.target_id
                if tid in in_degree:
                    in_degree[tid] -= 1
                    if in_degree[tid] == 0:
                        queue.append(tid)

        return order

    # ── Snapshot / DTO ───────────────────────────────────────────────

    def to_dto(self) -> DependencyGraphDTO:
        roots = [n.id for n in self.find_roots()]
        leaves = [n.id for n in self.find_leaves()]
        has_cycle, cycle_path = self._has_cycle_dfs()
        try:
            order = self.execution_order()
        except CycleError:
            order = []
        return DependencyGraphDTO(
            nodes=tuple(self._nodes.values()),
            edges=tuple(
                e for edges in self._edges.values() for e in edges
            ),
            roots=tuple(roots),
            leaves=tuple(leaves),
            has_cycle=has_cycle,
            cycle_path=tuple(cycle_path),
            execution_order=tuple(order),
            node_count=len(self._nodes),
            edge_count=sum(len(v) for v in self._edges.values()),
        )

    # ── Bulk Add ─────────────────────────────────────────────────────

    def add_from_proposals(self, proposals: list[dict[str, Any]]) -> None:
        """
        Bulk-add nodes & edges from proposal dicts.

        Expected keys per proposal:
          - id: str
          - title: str (optional)
          - depends_on: list[str] (optional)
          - blocks: list[str] (optional)
          - requires: list[str] (optional)
        """
        for p in proposals:
            pid = p["id"]
            self.add_node(pid, NodeKind.PROPOSAL, label=p.get("title", ""))
            for dep_id in p.get("depends_on", []):
                self.add_node(dep_id, NodeKind.PROPOSAL)
                # pid DEPENDS_ON dep_id -> edge dari dep_id ke pid
                self.add_edge(dep_id, pid, EdgeKind.DEPENDS_ON)
            for block_id in p.get("blocks", []):
                self.add_node(block_id, NodeKind.PROPOSAL)
                self.add_edge(pid, block_id, EdgeKind.BLOCKS)
            for req_id in p.get("requires", []):
                self.add_node(req_id, NodeKind.RESOURCE)
                self.add_edge(pid, req_id, EdgeKind.REQUIRES)
