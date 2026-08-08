# Federation Intelligence API - WP-28
# IP-3.4-003 (AO-3.4-001, paket ketiga - Distributed Governance Intelligence)
#
# Facade read-only untuk Distributed Governance Intelligence.
#
# Saat ini federation dapat saling percaya dan bekerja sama; IP-3.4-003
# menambahkan kemampuan untuk REASONING BERSAMA: tiap federation reasoning
# lokal, lalu reasoning dipertukarkan sebagai evidence (bukan authority),
# diagregasi menjadi insight, dan diturunkan menjadi rekomendasi.
#
# API menyediakan:
#   describe_collaboration()  - deskripsi kolaborasi (WP-21)
#   assess-alignment          - penilaian keselarasan kolaborasi (WP-21)
#   propose_collaboration()   - proposal kerja sama (WP-22)
#   package_knowledge()       - bungkus knowledge (WP-23)
#   read_knowledge()          - baca knowledge (WP-23)
#   build_evidence_graph()    - susun evidence graph (WP-24)
#   share_reasoning()         - bagikan reasoning lokal (WP-25)
#   synthesize_insight()      - agregasi reasoning lintas federation (WP-25)
#   recommend()               - rekomendasi federasi (WP-26)
#   explain_intelligence()    - penjelasan insight/rekomendasi (WP-27)
#
# TIDAK menyediakan: connect(), authorize(), execute(), sinkronisasi state.
# Seluruh output bersifat advisory/reasoning, bukan authority/aksi.

from typing import Any, Dict, Optional, Tuple

from sam.citizen.federation.collaboration import (
    CollaborationStatus,
    FederationCollaboration,
    FederationCollaborationModel,
)
from sam.citizen.federation.proposal import (
    CollaborationProposalEngine,
    CollaborationProposalResult,
)
from sam.citizen.federation.knowledge_exchange import (
    DistributedKnowledgeExchange,
    KnowledgeArtifact,
    KnowledgePackage,
)
from sam.citizen.federation.evidence_exchange import (
    DistributedEvidenceExchange,
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
)
from sam.citizen.federation.intelligence import (
    FederationInsight,
    FederationIntelligenceEngine,
    LocalReasoning,
)
from sam.citizen.federation.recommendation import (
    DistributedRecommendation,
    RecommendationResult,
)
from sam.citizen.federation.explainability import (
    FederationIntelligenceExplainer,
    IntelligenceExplanation,
)


class FederationIntelligenceAPI:
    """Facade read-only Distributed Governance Intelligence.

    Seluruh method = reasoning/assessment/advisory. TIDAK ada yang memberi
    kewenangan, TIDAK ada eksekusi, TIDAK ada sinkronisasi state.
    """

    def __init__(
        self,
        collaboration: Optional[FederationCollaborationModel] = None,
        proposal: Optional[CollaborationProposalEngine] = None,
        knowledge: Optional[DistributedKnowledgeExchange] = None,
        evidence: Optional[DistributedEvidenceExchange] = None,
        intelligence: Optional[FederationIntelligenceEngine] = None,
        recommendation: Optional[DistributedRecommendation] = None,
        explainer: Optional[FederationIntelligenceExplainer] = None,
    ) -> None:
        self._collab = collaboration or FederationCollaborationModel()
        self._proposal = proposal or CollaborationProposalEngine()
        self._knowledge = knowledge or DistributedKnowledgeExchange()
        self._evidence = evidence or DistributedEvidenceExchange()
        self._intel = intelligence or FederationIntelligenceEngine()
        self._recommend = recommendation or DistributedRecommendation()
        self._explain = explainer or FederationIntelligenceExplainer()

    # --- collaboration (WP-21) ------------------------------------------

    def describe_collaboration(
        self,
        source_id: str,
        target_id: str,
        purpose: str,
        shared_contracts: Tuple[str, ...] = (),
        shared_capabilities: Tuple[str, ...] = (),
        constraints: Tuple[str, ...] = (),
    ) -> FederationCollaboration:
        return self._collab.describe(
            source_id, target_id, purpose,
            shared_contracts, shared_capabilities, constraints)

    def assess_alignment(
        self,
        collaboration: FederationCollaboration,
        local_contracts: Tuple[str, ...],
        local_capabilities: Tuple[str, ...],
    ) -> CollaborationStatus:
        return self._collab.assess_alignment(
            collaboration, local_contracts, local_capabilities)

    # --- proposal (WP-22) ---------------------------------------------------

    def propose_collaboration(
        self,
        source_id: str,
        target_id: str,
        requested_capability: str,
        target_capabilities: Tuple[str, ...],
        target_contracts: Tuple[str, ...] = (),
        required_contracts: Tuple[str, ...] = (),
    ) -> CollaborationProposalResult:
        return self._proposal.propose(
            source_id, target_id, requested_capability,
            target_capabilities, target_contracts, required_contracts)

    # --- knowledge exchange (WP-23) -----------------------------------------

    def package_knowledge(
        self,
        source_id: str,
        artifacts: Tuple[KnowledgeArtifact, ...],
    ) -> KnowledgePackage:
        return self._knowledge.package(source_id, artifacts)

    def read_knowledge(
        self,
        package: KnowledgePackage,
        kinds: Tuple[str, ...] = (),
        keys: Tuple[str, ...] = (),
    ) -> Tuple[KnowledgeArtifact, ...]:
        return self._knowledge.read(package, kinds, keys)

    # --- evidence exchange (WP-24) ------------------------------------------

    def build_evidence_graph(
        self,
        source_id: str,
        nodes: Tuple[EvidenceNode, ...] = (),
        edges: Tuple[EvidenceEdge, ...] = (),
    ) -> EvidenceGraph:
        return self._evidence.build_graph(source_id, nodes, edges)

    def evidence_supporting(
        self,
        graph: EvidenceGraph,
        claim_node_id: str,
    ) -> Tuple[EvidenceNode, ...]:
        return self._evidence.supports(graph, claim_node_id)

    # --- reasoning & insight (WP-25) ----------------------------------------

    def share_reasoning(
        self,
        member_id: str,
        assessment: str,
        confidence: float,
        reasons: Tuple[str, ...] = (),
        trusted: bool = False,
    ) -> LocalReasoning:
        return LocalReasoning(
            member_id=member_id,
            assessment=assessment,
            confidence=confidence,
            reasons=reasons,
            trusted=trusted,
        )

    def synthesize_insight(
        self,
        focus: str,
        local_reasonings: Tuple[LocalReasoning, ...],
    ) -> FederationInsight:
        return self._intel.aggregate(focus, local_reasonings)

    def evidence_observations(
        self,
        graph: EvidenceGraph,
    ) -> Tuple[str, ...]:
        return self._intel.incorporate_evidence_graph(graph)

    # --- recommendation (WP-26) ---------------------------------------------

    def recommend(
        self,
        insights: Tuple[FederationInsight, ...],
    ) -> RecommendationResult:
        return self._recommend.recommend(insights)

    def recommend_for_member(
        self,
        member_id: str,
        insights: Tuple[FederationInsight, ...],
    ):
        return self._recommend.for_member(member_id, insights)

    # --- explainability (WP-27) ---------------------------------------------

    def explain_intelligence(
        self,
        insight: FederationInsight,
    ) -> IntelligenceExplanation:
        return self._explain.explain_insight(insight)

    def explain_recommendation(
        self,
        recommendation,
    ) -> IntelligenceExplanation:
        return self._explain.explain_recommendation(recommendation)
