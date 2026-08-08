"""gateway — WP-10 (IP-3.1-001).

Intelligence Gateway: the single entry point the operator talks to.

    ask()       : ask a question -> EvidenceChain/Answer (WP-04).
    explain()   : explain a decision -> DecisionExplanation (WP-06).
    trace()     : trace a claim -> Citations (WP-04).
    recommend() : issue an evidence-backed Recommendation (WP-12).

Per directive: the gateway must NOT access runtime directly. Everything
flows through repositories (WP-02). The gateway is a thin composition root
that wires repositories + resolvers + reasoner + explanation + recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sam.governance_intelligence.explanation.decision import DecisionExplanation, build_explanation, explanation_summary
from sam.governance_intelligence.knowledge.query import KnowledgeQueryAPI, QueryResult
from sam.governance_intelligence.knowledge.repository import (
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    QueryOnlyRepository,
    RuntimeRepository,
)
from sam.governance_intelligence.reasoning.engine.reasoner import GovernanceReasoner, ReasoningTree, Rule
from sam.governance_intelligence.reasoning.evidence import Citation, EvidenceResolver


@dataclass(frozen=True)
class IntelligenceResponse:
    kind: str  # 'answer' | 'explanation' | 'trace' | 'recommendation' | 'query'
    data: dict

    def public_dict(self) -> dict:
        return {"kind": self.kind, "data": self.data}


class IntelligenceGateway:
    """WP-10 implementation. Composition root only — no runtime access."""

    def __init__(
        self,
        mission_repo: MissionRepository,
        policy_repo: PolicyRepository,
        runtime_repo: RuntimeRepository,
        evidence_repo: EvidenceRepository,
        query_api: Optional[KnowledgeQueryAPI] = None,
        evidence_resolver: Optional[EvidenceResolver] = None,
        reasoner: Optional[GovernanceReasoner] = None,
    ) -> None:
        self._mission = mission_repo
        self._policy = policy_repo
        self._runtime = runtime_repo
        self._evidence = evidence_repo
        self._query = query_api or KnowledgeQueryAPI()
        self._ev_resolver = evidence_resolver or EvidenceResolver(evidence_repo)
        self._reasoner = reasoner or GovernanceReasoner(mission_repo)

    # --- ask: question -> answer ------------------------------------------
    def ask(self, question: str) -> IntelligenceResponse:
        chain = self._ev_resolver.resolve(question)
        return IntelligenceResponse(kind="answer", data=chain.public_dict())

    # --- explain: decision -> DecisionExplanation --------------------------
    def explain(
        self,
        goal: str,
        rules: List[tuple],
    ) -> IntelligenceResponse:
        tree = self._reasoner.reason(goal, rules, self._evidence)
        explanation = build_explanation(tree)
        return IntelligenceResponse(
            kind="explanation",
            data={
                **explanation.public_dict(),
                "summary": explanation_summary(explanation),
            },
        )

    # --- trace: claim -> citations -----------------------------------------
    def trace(self, claim: str) -> IntelligenceResponse:
        citations = self._ev_resolver.trace(claim)
        return IntelligenceResponse(
            kind="trace",
            data={"claim": claim, "citations": [c.public_dict() for c in citations]},
        )

    # --- recommend: evidence-backed recommendation (WP-12) ------------------
    def recommend(self, goal: str, rules: List[tuple]) -> IntelligenceResponse:
        tree = self._reasoner.reason(goal, rules, self._evidence)
        explanation = build_explanation(tree)
        rec = RecommendationService(self._evidence).build(goal, explanation)
        return IntelligenceResponse(kind="recommendation", data=rec.public_dict())

    # --- generic query -------------------------------------------------------
    def search(self, repo: QueryOnlyRepository, term: str) -> IntelligenceResponse:
        result = self._query.search(repo, term)
        return IntelligenceResponse(kind="query", data=result.jsonable())


from sam.governance_intelligence.recommendation import RecommendationService  # noqa: E402
