"""Knowledge Federation — Sprint 31.

Principles:
  - Move Knowledge, Not Data
  - Trust-based federation
  - Provenance-aware
  - Sovereignty-respecting
"""

from sam.federation.manager import FederationManager
from sam.federation.protocol import (
    FederationProtocol,
    KnowledgeOffer,
    KnowledgeRequest,
    FederationMessage,
)
from sam.federation.trust import TrustManager, ClusterTrust
from sam.federation.conflict import ConflictResolver, ConflictResult
from sam.federation.provenance import Provenance, ProvenanceManager
from sam.federation.consensus import ConsensusEngine, ConsensusVote
from sam.federation.sovereignty import (
    SovereigntyManager,
    SovereigntyPolicy,
    SharingPolicy,
)

__all__ = [
    "ClusterTrust",
    "ConflictResolver",
    "ConflictResult",
    "ConsensusEngine",
    "ConsensusVote",
    "FederationManager",
    "FederationMessage",
    "FederationProtocol",
    "KnowledgeOffer",
    "KnowledgeRequest",
    "Provenance",
    "ProvenanceManager",
    "SharingPolicy",
    "SovereigntyManager",
    "SovereigntyPolicy",
    "TrustManager",
]
