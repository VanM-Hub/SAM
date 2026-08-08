"""WP-28 - Governance Relationship Explorer (IP-3.1-003).

Produces the internal visual MODEL of governance relationships as an
immutable graph DTO. It does NOT generate a UI - it only builds the graph
(data structure) that a UI layer could later render.

Nodes: Mission, Workflow, Policy, Runtime, Recommendation, ADR,
       Architecture Order.
Edges: typed, deterministic relationships between those nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)


@dataclass(frozen=True)
class RelNode:
    id: str
    kind: str  # Mission | Workflow | Policy | Runtime | Recommendation | ADR | Architecture Order
    title: str

    def public_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "title": self.title}


@dataclass(frozen=True)
class RelEdge:
    source: str
    target: str
    relation: str  # e.g. "governs", "grounds", "implements", "requires"

    def public_dict(self) -> dict:
        return {"source": self.source, "target": self.target, "relation": self.relation}


@dataclass(frozen=True)
class RelationshipGraph:
    """Immutable governance relationship graph DTO (WP-28)."""

    nodes: List[RelNode] = field(default_factory=list)
    edges: List[RelEdge] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {
            "nodes": [n.public_dict() for n in self.nodes],
            "edges": [e.public_dict() for e in self.edges],
        }


class GovernanceRelationshipEngine:
    """WP-28 implementation. Builds the relationship graph deterministically."""

    NODE_KINDS = ("Mission", "Workflow", "Policy", "Runtime", "Recommendation", "ADR", "Architecture Order")

    def __init__(
        self,
        mission: MissionRepository,
        workflow: RuntimeRepository,
        policy: PolicyRepository,
        runtime: RuntimeRepository,
        evidence: EvidenceRepository,
        adr: ADRRepository,
        recommendation_items: Optional[List[KnowledgeItem]] = None,
    ) -> None:
        self._mission = mission
        self._workflow = workflow
        self._policy = policy
        self._runtime = runtime
        self._evidence = evidence
        self._adr = adr
        self._recommendations = recommendation_items or []

    def build(self) -> RelationshipGraph:
        nodes: List[RelNode] = []
        edges: List[RelEdge] = []
        _add = nodes.append
        _edge = edges.append

        # Mission nodes
        mission_ids: List[str] = []
        for it in self._mission.all():
            nid = f"mission:{it.key}"
            mission_ids.append(nid)
            _add(RelNode(nid, "Mission", it.title))
        # Workflow nodes
        workflow_ids: List[str] = []
        for it in self._workflow.all():
            nid = f"workflow:{it.key}"
            workflow_ids.append(nid)
            _add(RelNode(nid, "Workflow", it.title))
        # Policy nodes
        policy_ids: List[str] = []
        for it in self._policy.all():
            nid = f"policy:{it.key}"
            policy_ids.append(nid)
            _add(RelNode(nid, "Policy", it.title))
        # Runtime nodes
        runtime_ids: List[str] = []
        for it in self._runtime.all():
            nid = f"runtime:{it.key}"
            runtime_ids.append(nid)
            _add(RelNode(nid, "Runtime", it.title))
        # Recommendation nodes
        rec_ids: List[str] = []
        for it in self._recommendations:
            nid = f"recommendation:{it.key}"
            rec_ids.append(nid)
            _add(RelNode(nid, "Recommendation", it.title))
        # ADR nodes
        adr_ids: List[str] = []
        for it in self._adr.accepted():
            nid = f"adr:{it.key}"
            adr_ids.append(nid)
            _add(RelNode(nid, "ADR", it.title))
        # Architecture Order nodes
        ao_ids: List[str] = []
        for it in self._arch_orders():
            nid = f"archorder:{it.key}"
            ao_ids.append(nid)
            _add(RelNode(nid, "Architecture Order", it.title))

        # Edges - deterministic relationships
        for wid in workflow_ids:
            for mid in mission_ids:
                _edge(RelEdge(wid, mid, "implements"))
        for pid in policy_ids:
            for wid in workflow_ids:
                _edge(RelEdge(pid, wid, "governs"))
        for rid in runtime_ids:
            for wid in workflow_ids:
                _edge(RelEdge(rid, wid, "executes"))
        for rec in rec_ids:
            for pid in policy_ids:
                _edge(RelEdge(rec, pid, "grounded_in"))
        for adr in adr_ids:
            for pid in policy_ids:
                _edge(RelEdge(adr, pid, "grounds"))
        for ao in ao_ids:
            for adr in adr_ids:
                _edge(RelEdge(ao, adr, "authorizes"))

        return RelationshipGraph(nodes=nodes, edges=edges)

    def _arch_orders(self) -> List[KnowledgeItem]:
        orders = []
        for it in self._adr.all():
            meta = it.metadata or {}
            if meta.get("kind") == "arch_order" or "architecture order" in it.section.lower():
                orders.append(it)
        return orders
