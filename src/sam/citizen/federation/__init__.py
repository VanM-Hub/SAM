# Federation - IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
# WP-01..10 (+ WP-11..20 IP-3.4-002 Federation Trust & Interoperability
# + WP-21..30 IP-3.4-003 Distributed Governance Intelligence
# + WP-31..40 IP-3.4-004 Operational Coordination & Ecosystem Readiness)
#
# Layer: mengakui & bertukar capability antar beberapa Citizen Ecosystem yang
# berdaulat (sovereign) melalui contract. KEPUTUSAN ARSITEKTUR KUNCI:
# Federation != Distributed Runtime.
#
# Federation TIDAK berarti: remote execution, distributed scheduler,
# distributed runtime, global governance.
# Federation BERARTI: beberapa Citizen Ecosystem berdaulat saling MENGENALI
# dan BERTUKAR capability melalui contract (deskriptif, bukan eksekusi).
#
# IP-3.4-003 (Distributed Governance Intelligence): tiap federation reasoning
# secara lokal, reasoning dipertukarkan sebagai EVIDENCE (bukan authority),
# diagregasi secara deterministik menjadi insight, diturunkan jadi rekomendasi.
# BUKAN Distributed Governance, BUKAN Shared Governance.
#
# Guardrail IP-3.4-001 dikunci (compliance.py FED-01..10):
#   Federation != Central Governance; Registry != Control Plane;
#   Capability Exchange != Execution; Discovery != Connection;
#   Health != Monitoring Control; Descriptor != Contract Execution;
#   Federation Identity != Global Identity; Sovereignty First.
#
# Guardrail IP-3.4-002 (Federation Trust & Interoperability):
#   Trust != Authority; Interoperability != Execution;
#   Negotiation != Agreement; Assessment != Federation Control;
#   Compatibility != Approval; Local Sovereignty; Registry authoritative;
#   Deterministic; Evidence-first.
#
# Guardrail IP-3.4-003 (Distributed Governance Intelligence):
#   Knowledge != Authority; Evidence Exchange != Runtime Sharing;
#   Recommendation != Decision; Collaboration != Execution;
#   Federation Intelligence != Central Intelligence; Sovereignty preserved;
#   Deterministic reasoning; Evidence-first; Read-only API; No hidden dependency.
#
# IP-3.4-004 (Federation Operational Coordination & Ecosystem Readiness):
#   federation mengetahui apakah kolaborasi lintas-ekosistem LAYAK, tetapi
#   TIDAK pernah memulai kolaborasi otomatis. Output = readiness assessment /
#   coordination insight / federation health / recommendation / explanation.
#   BUKAN distributed execution, BUKAN distributed scheduling.
#
# Guardrail IP-3.4-004 (compliance.py OR-01..10):
#   Readiness != Execution; Coordination != Orchestration;
#   Recommendation != Command; Aggregation != Authority;
#   Federation Health != Runtime Control; Local sovereignty preserved;
#   Registry remains authoritative; Evidence-first readiness;
#   Deterministic aggregation; Read-only operational API.

# WP-01 - Federation Identity
from sam.citizen.federation.identity import (
    FederationIdentity,
    FederationMember,
    FederationInstance,
)

# WP-02 - Federation Registry
from sam.citizen.federation.registry import FederationRegistry

# WP-03 - Federation Discovery
from sam.citizen.federation.discovery import FederationDiscovery

# WP-04 - Federation Descriptor
from sam.citizen.federation.descriptor import (
    FederationDescriptor,
    build_federation_descriptor,
)

# WP-05 - Capability Exchange
from sam.citizen.federation.capability_exchange import (
    CapabilityAdvertisement,
    CapabilityExchange,
)

# WP-06 - Federation Health
from sam.citizen.federation.health import (
    FederationHealth,
    FederationHealthAssessor,
)

# WP-07 - Federation API
from sam.citizen.federation.api import FederationAPI

# WP-11..20 - Federation Trust & Interoperability (IP-3.4-002)
from sam.citizen.federation.trust import (
    FederationTrustProfile,
    TrustLevel,
    TrustEvidence,
    TrustConstraint,
)
from sam.citizen.federation.trust_engine import (
    TrustEvaluationEngine,
    TrustAggregator,
)
from sam.citizen.federation.interoperability import (
    InteroperabilityAssessment,
    InteroperabilityEngine,
)
from sam.citizen.federation.negotiation import (
    NegotiationProposal,
    NegotiationResult,
    CapabilityNegotiator,
)
from sam.citizen.federation.compatibility import (
    FederationCompatibility,
    FederationCompatibilityItem,
    FederationCompatibilityAnalyzer,
)
from sam.citizen.federation.explainability import (
    TrustExplanation,
    InteropExplanation,
    TrustExplainer,
)
from sam.citizen.federation.interop_api import FederationInteroperabilityAPI

# WP-21..30 - Distributed Governance Intelligence (IP-3.4-003)
from sam.citizen.federation.collaboration import (
    FederationCollaboration,
    CollaborationStatus,
    FederationCollaborationModel,
)
from sam.citizen.federation.proposal import (
    CollaborationProposal,
    CollaborationProposalResult,
    CollaborationProposalEngine,
)
from sam.citizen.federation.knowledge_exchange import (
    KnowledgeArtifact,
    KnowledgePackage,
    DistributedKnowledgeExchange,
)
from sam.citizen.federation.evidence_exchange import (
    EvidenceNode,
    EvidenceEdge,
    EvidenceGraph,
    DistributedEvidenceExchange,
)
from sam.citizen.federation.intelligence import (
    LocalReasoning,
    FederationInsight,
    FederationIntelligenceEngine,
)
from sam.citizen.federation.recommendation import (
    FederationRecommendation,
    RecommendationResult,
    DistributedRecommendation,
)
from sam.citizen.federation.explainability import (
    IntelligenceExplanation,
    FederationIntelligenceExplainer,
)
from sam.citizen.federation.intelligence_api import FederationIntelligenceAPI

# WP-31..38 - Federation Operational Coordination & Ecosystem Readiness (IP-3.4-004)
from sam.citizen.federation.operational_readiness import (
    FederationReadiness,
    FederationOperationalModel,
    READINESS_DIMENSIONS,
    categorize_overall,
)
from sam.citizen.federation.aggregation import (
    FederationReadinessAggregate,
    FederationReadinessAggregator,
)
from sam.citizen.federation.coordination_intelligence import (
    CoordinationInsight,
    CoordinationIntelligence,
)
from sam.citizen.federation.risk import (
    FederationRisk,
    FederationRiskAssessment,
    FederationRiskAssessor,
)
from sam.citizen.federation.recommendation import (
    CoordinationRecommendation,
    CoordinationRecommendationResult,
    CoordinationRecommendationEngine,
)
from sam.citizen.federation.explainability import (
    ReadinessExplanation,
    CoordinationExplanation,
    FederationOperationalExplainer,
)
from sam.citizen.federation.operational_api import (
    FederationOperationalAPI,
)

__version__ = "3.6.0"

__all__ = [
    "FederationIdentity", "FederationMember", "FederationInstance",
    "FederationRegistry",
    "FederationDiscovery",
    "FederationDescriptor", "build_federation_descriptor",
    "CapabilityAdvertisement", "CapabilityExchange",
    "FederationHealth", "FederationHealthAssessor",
    "FederationAPI",
    # IP-3.4-002
    "FederationTrustProfile", "TrustLevel", "TrustEvidence", "TrustConstraint",
    "TrustEvaluationEngine", "TrustAggregator",
    "InteroperabilityAssessment", "InteroperabilityEngine",
    "NegotiationProposal", "NegotiationResult", "CapabilityNegotiator",
    "FederationCompatibility", "FederationCompatibilityItem",
    "FederationCompatibilityAnalyzer",
    "TrustExplanation", "InteropExplanation", "TrustExplainer",
    "FederationInteroperabilityAPI",
    # IP-3.4-003
    "FederationCollaboration", "CollaborationStatus",
    "FederationCollaborationModel",
    "CollaborationProposal", "CollaborationProposalResult",
    "CollaborationProposalEngine",
    "KnowledgeArtifact", "KnowledgePackage", "DistributedKnowledgeExchange",
    "EvidenceNode", "EvidenceEdge", "EvidenceGraph",
    "DistributedEvidenceExchange",
    "LocalReasoning", "FederationInsight", "FederationIntelligenceEngine",
    "FederationRecommendation", "RecommendationResult",
    "DistributedRecommendation",
    "IntelligenceExplanation", "FederationIntelligenceExplainer",
    "FederationIntelligenceAPI",
    # IP-3.4-004
    "FederationReadiness", "FederationOperationalModel",
    "READINESS_DIMENSIONS", "categorize_overall",
    "FederationReadinessAggregate", "FederationReadinessAggregator",
    "CoordinationInsight", "CoordinationIntelligence",
    "FederationRisk", "FederationRiskAssessment", "FederationRiskAssessor",
    "CoordinationRecommendation", "CoordinationRecommendationResult",
    "CoordinationRecommendationEngine",
    "ReadinessExplanation", "CoordinationExplanation",
    "FederationOperationalExplainer",
    "FederationOperationalAPI",
]
