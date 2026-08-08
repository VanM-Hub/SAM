"""WP-22 - Intelligence API v2 (IP-3.1-002).

Extends the gateway with contextual reasoning methods:

    ask()        : (inherited v1) question -> answer
    explain()    : (inherited v1) decision -> explanation
    trace()      : (inherited v1) claim -> citations
    recommend()  : (inherited v1) evidence-backed recommendation
    understand() : resolve cross-domain GovernanceContext (WP-16) + trust
    why()        : full deterministic evidence trace (WP-18)
    how()        : fixed-structure explanation (WP-19)
    what_if()    : pure reasoning simulation, NEVER changes governance (WP-22)

api_v2 wires the contextual engines (context, reference_graph, trace,
explanation.composer, trust) on top of the v1 gateway. Read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sam.governance_intelligence.context import ContextResolutionEngine, GovernanceContext
from sam.governance_intelligence.explanation.composer import ExplanationComposer, StructuredExplanation
from sam.governance_intelligence.gateway import IntelligenceGateway, IntelligenceResponse
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)
from sam.governance_intelligence.reasoning.engine.reasoner import ReasoningTree
from sam.governance_intelligence.reference_graph import CrossReferenceEngine, ReferenceGraph
from sam.governance_intelligence.simulation import SimulationResult, WhatIfSimulator
from sam.governance_intelligence.trace import EvidenceTrace, EvidenceTraceEngine
from sam.governance_intelligence.trust import TrustAssessment, TrustScoreEngine


@dataclass(frozen=True)
class IntelligenceResponseV2:
    kind: str  # 'understanding' | 'why' | 'how' | 'what_if' | 'graph' | 'trust'
    data: dict

    def public_dict(self) -> dict:
        return {"kind": self.kind, "data": self.data}


class IntelligenceGatewayV2:
    """WP-22 composition root. Wires WP-16..21 on top of v1 gateway."""

    def __init__(
        self,
        gateway: IntelligenceGateway,
        mission: MissionRepository,
        policy: PolicyRepository,
        runtime: RuntimeRepository,
        evidence: EvidenceRepository,
        adr: ADRRepository,
        workflow: Optional[RuntimeRepository] = None,
    ) -> None:
        self._gw = gateway
        self._mission = mission
        self._policy = policy
        self._runtime = runtime
        self._evidence = evidence
        self._adr = adr
        self._workflow = workflow or runtime
        self._context = ContextResolutionEngine(
            mission, self._workflow, runtime, policy, evidence, adr
        )
        self._trace = EvidenceTraceEngine(mission, policy, evidence, adr, runtime)
        self._composer = ExplanationComposer()
        self._trust = TrustScoreEngine(evidence)
        self._what_if = WhatIfSimulator(evidence)

    # --- understand: resolve cross-domain context + trust ------------------
    def understand(self) -> IntelligenceResponseV2:
        ctx = self._context.resolve()
        trust = self._trust.assess(self._evidence.all())
        return IntelligenceResponseV2(
            kind="understanding",
            data={"context": ctx.public_dict(), "trust": trust.public_dict()},
        )

    # --- why: full deterministic evidence trace -----------------------------
    def why(self, recommendation_key: str) -> IntelligenceResponseV2:
        trace = self._trace.trace_recommendation(recommendation_key)
        return IntelligenceResponseV2(kind="why", data=trace.public_dict())

    # --- how: fixed-structure explanation (WP-19) ---------------------------
    def how(self, tree: ReasoningTree, governance_basis: Optional[List[str]] = None,
            architectural_basis: Optional[List[str]] = None) -> IntelligenceResponseV2:
        # reuse v1 evidence resolver chain for the evidence field
        chain = self._gw._ev_resolver.resolve(tree.goal if hasattr(tree, "goal") else "decision")
        expl = self._composer.compose(
            tree,
            chain=chain,
            governance_basis=governance_basis,
            architectural_basis=architectural_basis,
        )
        return IntelligenceResponseV2(kind="how", data=expl.public_dict())

    # --- what_if: pure reasoning simulation (never changes governance) ------
    def what_if(self, missing_evidence: str) -> IntelligenceResponseV2:
        res = self._what_if.simulate_missing(missing_evidence)
        assert res.governance_unchanged is True
        return IntelligenceResponseV2(kind="what_if", data=res.public_dict())

    # --- reference graph ------------------------------------------------------
    def reference_graph(self) -> IntelligenceResponseV2:
        engine = CrossReferenceEngine(
            mission_items=self._mission.all(),
            workflow_items=self._workflow.all(),
            policy_items=self._policy.all(),
            evidence_items=self._evidence.all(),
            adr_items=self._adr.accepted(),
            recommendation_items=[],  # recommendations are derived, not stored as artifacts
        )
        graph = engine.build()
        return IntelligenceResponseV2(kind="graph", data=graph.public_dict())

    # --- passthrough to v1 (compat) -------------------------------------------
    def ask(self, question: str) -> IntelligenceResponse:
        return self._gw.ask(question)

    def trace(self, claim: str) -> IntelligenceResponse:
        return self._gw.trace(claim)

    def recommend(self, goal: str, rules: List[tuple]) -> IntelligenceResponse:
        return self._gw.recommend(goal, rules)
