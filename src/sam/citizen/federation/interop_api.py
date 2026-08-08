# Federation Interoperability API - WP-17
# IP-3.4-002 (AO-3.4-001 / ED-3.4-001, paket kedua)
#
# Facade read-only untuk trust, interoperability, negosiasi, dan penjelasan.
#
# API menyediakan:
#   trust()            - profil trust
#   interoperability() - penilaian interoperabilitas
#   negotiate()        - proposal negosiasi
#   explain()          - penjelasan trust/interoperability
#
# TIDAK menyediakan: connect(), authorize(), execute().
# Seluruh output bersifat assessment/advisory, bukan authority/aksi.

from typing import Any, Dict, Optional, Tuple

from sam.citizen.federation.trust import (
    FederationTrustProfile,
    TrustConstraint,
    TrustEvidence,
)
from sam.citizen.federation.trust_engine import (
    TrustAggregator,
    TrustEvaluationEngine,
)
from sam.citizen.federation.interoperability import (
    InteroperabilityAssessment,
    InteroperabilityEngine,
)
from sam.citizen.federation.negotiation import (
    CapabilityNegotiator,
    NegotiationResult,
)
from sam.citizen.federation.explainability import (
    InteropExplanation,
    TrustExplanation,
    TrustExplainer,
)


class FederationInteroperabilityAPI:
    """Facade read-only Federation Trust & Interoperability.

    Seluruh method = assessment/advisory. TIDAK ada yang memberi kewenangan,
    tidak ada yang menjalankan aksi, tidak ada yang mengikat.
    """

    def __init__(
        self,
        trust_engine: Optional[TrustEvaluationEngine] = None,
        interop_engine: Optional[InteroperabilityEngine] = None,
        negotiator: Optional[CapabilityNegotiator] = None,
        explainer: Optional[TrustExplainer] = None,
        aggregator: Optional[TrustAggregator] = None,
    ) -> None:
        self._trust = trust_engine or TrustEvaluationEngine()
        self._interop = interop_engine or InteroperabilityEngine()
        self._negotiate = negotiator or CapabilityNegotiator()
        self._explain = explainer or TrustExplainer()
        self._aggregate = aggregator or TrustAggregator()

    # --- trust --------------------------------------------------------

    def trust(
        self,
        member_id: str,
        certification: Optional[str] = None,
        compatibility: Optional[str] = None,
        contract: Tuple[str, ...] = (),
        health: Optional[str] = None,
        evidence: Tuple[TrustEvidence, ...] = (),
        constraints: Tuple[TrustConstraint, ...] = (),
    ) -> FederationTrustProfile:
        return self._trust.evaluate(
            member_id=member_id,
            certification=certification,
            compatibility=compatibility,
            contract=contract,
            health=health,
            explicit_evidence=evidence,
            constraints=constraints,
        )

    def trust_summary(self, profiles: Tuple[FederationTrustProfile, ...]) -> Dict[str, Any]:
        return self._aggregate.aggregate(profiles)

    # --- interoperability ----------------------------------------------

    def interoperability(
        self,
        source_id: str,
        target_id: str,
        source_contracts: Tuple[str, ...],
        target_contracts: Tuple[str, ...],
        source_capabilities: Tuple[str, ...],
        target_capabilities: Tuple[str, ...],
        source_cert: Optional[str] = None,
        target_cert: Optional[str] = None,
    ) -> InteroperabilityAssessment:
        return self._interop.assess(
            source_id=source_id,
            target_id=target_id,
            source_contracts=source_contracts,
            target_contracts=target_contracts,
            source_capabilities=source_capabilities,
            target_capabilities=target_capabilities,
            source_cert=source_cert,
            target_cert=target_cert,
        )

    # --- negotiation -----------------------------------------------------

    def negotiate(
        self,
        source_id: str,
        target_id: str,
        requested_capability: str,
        target_capabilities: Tuple[str, ...],
        target_contracts: Tuple[str, ...],
        source_contracts: Tuple[str, ...],
        shared_contracts: Tuple[str, ...],
    ) -> NegotiationResult:
        return self._negotiate.negotiate(
            source_id=source_id,
            target_id=target_id,
            requested_capability=requested_capability,
            target_capabilities=target_capabilities,
            target_contracts=target_contracts,
            source_contracts=source_contracts,
            shared_contracts=shared_contracts,
        )

    # --- explain -----------------------------------------------------------

    def explain_trust(self, profile: FederationTrustProfile) -> TrustExplanation:
        return self._explain.explain_profile(profile)

    def explain_interoperability(
        self,
        source_id: str,
        target_id: str,
        compatible: bool,
        gaps: Tuple[str, ...] = (),
        recommended: Tuple[str, ...] = (),
    ) -> InteropExplanation:
        return self._explain.explain_interoperability(
            source_id, target_id, compatible, gaps, recommended)
