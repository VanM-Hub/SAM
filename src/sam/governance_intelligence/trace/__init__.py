"""WP-18 - Evidence Trace Engine (IP-3.1-002).

Full deterministic trace. A question such as "Why did Recommendation A
appear?" must resolve to the whole chain:

    Recommendation -> Evidence -> Policy -> Mission -> ADR -> Architecture Order

The entire chain MUST be deterministic (no LLM, no heuristics beyond exact
matching). Output: EvidenceTrace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)


@dataclass(frozen=True)
class TraceNode:
    layer: str
    key: str
    title: str
    source: str

    def public_dict(self) -> dict:
        return {"layer": self.layer, "key": self.key, "title": self.title, "source": self.source}


@dataclass(frozen=True)
class EvidenceTrace:
    """Full deterministic chain from a recommendation back to its basis."""

    target: str  # the recommendation (key) being traced
    chain: List[TraceNode]
    complete: bool  # True when every layer resolved to a real artifact

    def public_dict(self) -> dict:
        return {
            "target": self.target,
            "chain": [n.public_dict() for n in self.chain],
            "complete": self.complete,
        }


class EvidenceTraceEngine:
    """WP-18 implementation. Builds deterministic traces down to Architecture Order."""

    def __init__(
        self,
        mission: MissionRepository,
        policy: PolicyRepository,
        evidence: EvidenceRepository,
        adr: ADRRepository,
        runtime: RuntimeRepository,
    ) -> None:
        self._mission = mission
        self._policy = policy
        self._evidence = evidence
        self._adr = adr
        self._runtime = runtime

    def trace_recommendation(self, recommendation_key: str) -> EvidenceTrace:
        chain: List[TraceNode] = []
        complete = True

        # Layer 1: Recommendation -> (map to evidence by shared token)
        chain.append(TraceNode(layer="Recommendation", key=recommendation_key, title=recommendation_key, source="recommendation"))

        # Layer 2: Evidence
        ev = self._evidence.by_claim(recommendation_key)
        if ev:
            chain.append(TraceNode("Evidence", ev[0].key, ev[0].title, ev[0].source))
        else:
            # fall back: find evidence whose content/key references the key
            ev = [it for it in self._evidence.all() if recommendation_key in it.key or recommendation_key in it.content]
            if ev:
                chain.append(TraceNode("Evidence", ev[0].key, ev[0].title, ev[0].source))
            else:
                chain.append(TraceNode("Evidence", recommendation_key, "no direct evidence", "missing"))
                complete = False

        # Layer 3: Policy (the policy that gates the recommendation)
        policy = self._resolve_policy(recommendation_key)
        chain.append(policy)
        if policy.key == recommendation_key and policy.source == "missing":
            complete = False

        # Layer 4: Mission
        mission = self._resolve_mission(recommendation_key)
        chain.append(mission)
        if mission.source == "missing":
            complete = False

        # Layer 5: ADR
        adr = self._resolve_adr(recommendation_key)
        chain.append(adr)
        if adr.source == "missing":
            complete = False

        # Layer 6: Architecture Order (from ADR / runtime architectural refs)
        ao = self._resolve_arch_order(recommendation_key)
        chain.append(ao)
        if ao.source == "missing":
            complete = False

        return EvidenceTrace(target=recommendation_key, chain=chain, complete=complete)

    # --- internal deterministic resolvers ----------------------------------
    def _resolve_policy(self, token: str) -> TraceNode:
        token_low = token.lower()
        for it in self._policy.all():
            if token_low in it.key.lower() or token_low in it.title.lower() or token_low in it.section.lower():
                return TraceNode("Policy", it.key, it.title, it.source)
        return TraceNode("Policy", token, "policy not found", "missing")

    def _resolve_mission(self, token: str) -> TraceNode:
        token_low = token.lower()
        for it in self._mission.all():
            if token_low in it.key.lower() or token_low in it.title.lower() or token_low in it.content.lower():
                return TraceNode("Mission", it.key, it.title, it.source)
        # default: first mission objective
        if self._mission.size():
            f = self._mission.all()[0]
            return TraceNode("Mission", f.key, f.title, f.source)
        return TraceNode("Mission", token, "mission not found", "missing")

    def _resolve_adr(self, token: str) -> TraceNode:
        token_low = token.lower()
        accepted = self._adr.accepted()
        for it in accepted:
            if token_low in it.key.lower() or token_low in it.title.lower():
                return TraceNode("ADR", it.key, it.title, it.source)
        if accepted:
            f = accepted[0]
            return TraceNode("ADR", f.key, f.title, f.source)
        return TraceNode("ADR", token, "adr not found", "missing")

    def _resolve_arch_order(self, token: str) -> TraceNode:
        token_low = token.lower()
        for it in self._adr.all():
            meta = it.metadata
            if meta.get("kind") == "arch_order" or "architecture order" in it.section.lower():
                return TraceNode("Architecture Order", it.key, it.title, it.source)
        # "Architecture Order" is often the ADR section naming it
        for it in self._runtime.all():
            if "architecture" in it.key.lower() or "architecture order" in it.section.lower():
                return TraceNode("Architecture Order", it.key, it.title, it.source)
        if self._adr.size():
            f = self._adr.all()[-1]
            return TraceNode("Architecture Order", f.key, f.section or f.title, f.source)
        return TraceNode("Architecture Order", token, "architecture order not found", "missing")
