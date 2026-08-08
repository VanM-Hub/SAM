"""WP-17 - Cross-Reference Engine (IP-3.1-002).

Connects every governance artifact into a deterministic reference graph:

    Mission -> Workflow -> Policy -> Evidence -> ADR -> Recommendation

The graph is built from explicit artifacts (Mission/Workflow/Policy/Evidence/
ADR/Recommendation items) and edges derived from key/section/content overlap
via exact matching. Read-only: it never mutates governance.

Output:

    ReferenceGraph
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from sam.governance_intelligence.knowledge.models import KnowledgeItem


@dataclass(frozen=True)
class ReferenceGraph:
    """Immutable directed graph of governance artifacts."""

    nodes: Tuple[str, ...]
    edges: Tuple[Tuple[str, str], ...]

    def public_dict(self) -> dict:
        return {
            "nodes": list(self.nodes),
            "edges": [[a, b] for a, b in self.edges],
        }

    def neighbors(self, node: str) -> List[str]:
        return [b for a, b in self.edges if a == node]

    def path(self, start: str, end: str) -> List[str]:
        """First deterministic path from start to end (BFS over edges)."""
        from collections import deque

        parent: Dict[str, str] = {start: None}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            if cur == end:
                break
            for nxt in self.neighbors(cur):
                if nxt not in parent:
                    parent[nxt] = cur
                    queue.append(nxt)
        if end not in parent:
            return []
        out: List[str] = []
        cur = end
        while cur is not None:
            out.append(cur)
            cur = parent.get(cur)
        out.reverse()
        return out


# Canonical layer order (deterministic layering for cross-referencing).
_LAYER_ORDER = ["Mission", "Workflow", "Policy", "Evidence", "ADR", "Recommendation"]


def _layer(kind: str) -> str:
    low = kind.lower()
    for name in _LAYER_ORDER:
        if name.lower() in low:
            return name
    return kind.title()


class CrossReferenceEngine:
    """WP-17 implementation. Builds a deterministic ReferenceGraph."""

    def __init__(
        self,
        mission_items: List[KnowledgeItem],
        workflow_items: List[KnowledgeItem],
        policy_items: List[KnowledgeItem],
        evidence_items: List[KnowledgeItem],
        adr_items: List[KnowledgeItem],
        recommendation_items: List[KnowledgeItem],
    ) -> None:
        self._sets: Dict[str, List[KnowledgeItem]] = {
            "Mission": mission_items,
            "Workflow": workflow_items,
            "Policy": policy_items,
            "Evidence": evidence_items,
            "ADR": adr_items,
            "Recommendation": recommendation_items,
        }

    def build(self) -> ReferenceGraph:
        nodes: Set[str] = set()
        edges: Set[Tuple[str, str]] = set()

        for layer, items in self._sets.items():
            for it in items:
                key = f"{layer}:{it.key}"
                nodes.add(key)

        # Connect within same artifact by key-chain and across layers by
        # overlapping reference tokens (exact key / section / title match).
        for layer, items in self._sets.items():
            for it in items:
                src = f"{layer}:{it.key}"
                matches = self._match(it)
                for other_layer, dst in matches:
                    edges.add((src, dst))

        return ReferenceGraph(
            nodes=tuple(sorted(nodes)),
            edges=tuple(sorted(edges)),
        )

    def _match(self, it: KnowledgeItem) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        tokens = [it.key, it.section, it.title]
        for layer, items in self._sets.items():
            if layer == _layer(it.kind):
                continue
            for other in items:
                if other.key == it.key or other.key == it.section:
                    out.append((layer, f"{layer}:{other.key}"))
                elif other.title and other.title in tokens:
                    out.append((layer, f"{layer}:{other.key}"))
        # dedupe
        seen: Set[Tuple[str, str]] = set()
        result = []
        for tup in out:
            if tup not in seen:
                seen.add(tup)
                result.append(tup)
        return result
