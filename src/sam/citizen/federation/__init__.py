# Federation - IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
# WP-01..10 (+ WP-11..20 IP-3.4-002 Federation Trust & Interoperability)
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
]
