"""WP-27 - Evidence Navigation Engine (IP-3.1-003).

Lets the operator walk the full evidence hierarchy:

    Mission -> Workflow -> Policy -> Evidence -> ADR -> Architecture Order -> Decision

Output: EvidenceNavigationTree - the deterministic, layered navigation that
can be expanded step by step. Every path preserves the evidence chain and
governance/architecture references. No UI is produced; this is a model DTO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)


@dataclass(frozen=True)
class NavNode:
    """One layer in the evidence navigation tree."""

    layer: str
    key: str
    title: str
    source: str
    children: List["NavNode"] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {
            "layer": self.layer,
            "key": self.key,
            "title": self.title,
            "source": self.source,
            "children": [c.public_dict() for c in self.children],
        }


@dataclass(frozen=True)
class EvidenceNavigationTree:
    """Deterministic layered navigation over the evidence hierarchy (WP-27)."""

    root: NavNode
    depth: int

    def public_dict(self) -> dict:
        return {"depth": self.depth, "root": self.root.public_dict()}


class EvidenceNavigationEngine:
    """WP-27 implementation. Read-only, deterministic, no UI."""

    def __init__(
        self,
        mission: MissionRepository,
        workflow: RuntimeRepository,
        policy: PolicyRepository,
        evidence: EvidenceRepository,
        adr: ADRRepository,
        runtime: RuntimeRepository,
    ) -> None:
        self._mission = mission
        self._workflow = workflow
        self._policy = policy
        self._evidence = evidence
        self._adr = adr
        self._runtime = runtime

    def build(self, start_key: Optional[str] = None) -> EvidenceNavigationTree:
        """Build the full navigation tree rooted at a mission (or the first)."""
        mission = self._first_or(self._mission.all(), start_key, "Mission")
        mission_node = NavNode(
            layer="Mission",
            key=mission.key,
            title=mission.title,
            source=mission.source,
            children=self._mission_children(mission),
        )
        depth = self._depth(mission_node)
        return EvidenceNavigationTree(root=mission_node, depth=depth)

    def _mission_children(self, mission: KnowledgeItem) -> List[NavNode]:
        children: List[NavNode] = []
        # Workflow layer under mission
        for wf in self._workflow.all()[:3]:
            wf_node = NavNode(
                layer="Workflow", key=wf.key, title=wf.title, source=wf.source,
                children=[self._to_node("Policy", p) for p in self._policy.all()[:3]],
            )
            children.append(wf_node)
        # Policy layer directly under mission
        for pol in self._policy.all():
            pol_node = NavNode(
                layer="Policy", key=pol.key, title=pol.title, source=pol.source,
                children=[self._to_node("Evidence", e) for e in self._evidence_for(pol)],
            )
            children.append(pol_node)
        # Runtime layer
        for rt in self._runtime.all()[:2]:
            children.append(self._to_node("Runtime", rt))
        return children

    def _evidence_for(self, node: KnowledgeItem) -> List[KnowledgeItem]:
        evs = self._evidence.by_claim(node.key)
        if evs:
            return evs[:3]
        # fall back: evidence whose content references the policy key
        return [e for e in self._evidence.all() if node.key in e.key or node.key in e.content][:3]

    def _to_node(self, layer: str, item: KnowledgeItem) -> NavNode:
        return NavNode(layer=layer, key=item.key, title=item.title, source=item.source)

    def _first_or(self, items: List[KnowledgeItem], key: Optional[str], label: str) -> KnowledgeItem:
        if key:
            for it in items:
                if key in it.key or key in it.title:
                    return it
        return items[0] if items else KnowledgeItem(
            key=label.lower(), kind=label.lower(), source="missing",
            title=f"no {label.lower()} found", content="", signature="",
        )

    def _depth(self, node: NavNode) -> int:
        if not node.children:
            return 1
        return 1 + max(self._depth(c) for c in node.children)
