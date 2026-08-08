# Citizen Collaboration API - WP-17
# IP-3.3-002 (AO-3.3-001 / ED-3.3-001 2nd cycle)
#
# Fasad read-only untuk collaboration & compatibility antar Citizen. Menjawab:
#   - Apa saja kolaborasi yang bisa diusulkan antar citizen?   -> propose
#   - Apakah dua citizen kompatibel? Mengapa?                  -> compatibility/explain
#   - Contract apa yang menyatukan mereka?                     -> resolve_contract
#   - Ada konflik dependency tidak?                            -> analyze_dependency
#   - Mengapa kolaborasi ini masuk akal?                       -> explain_collaboration
#
# Fasad MURNI read / proposal. TIDAK ada: form-collaboration, activate-channel,
# run-joint-capability, mutasi lifecycle/runtime/governance/foundation.

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Sequence

from sam.citizen.collaboration.models import (
    CollaborationSpec,
    CollaborationRole,
)
from sam.citizen.collaboration.proposal import (
    CollaborationProposal,
    CollaborationProposalEngine,
)
from sam.citizen.collaboration.compatibility import (
    CompatibilityReport,
    CompatibilityAnalyzer,
)
from sam.citizen.collaboration.contract_resolution import (
    ContractResolution,
    ContractResolutionEngine,
    ResolutionRequirement,
)
from sam.citizen.collaboration.dependency import (
    DependencyAnalysis,
    DependencyCompatibilityChecker,
)
from sam.citizen.collaboration.explainability import (
    CollaborationExplanation,
    CollaborationExplainer,
)


@dataclass(frozen=True)
class CollaborationSummary:
    """Ringkasan kolaborasi untuk dikonsumsi platform (immutable)."""

    collaboration_id: str
    participants: Tuple[str, ...]
    shared_capabilities: Tuple[str, ...]
    privilege_free: bool

    def as_dict(self) -> Dict[str, object]:
        return {
            "collaboration_id": self.collaboration_id,
            "participants": list(self.participants),
            "shared_capabilities": list(self.shared_capabilities),
            "privilege_free": self.privilege_free,
        }


class CitizenCollaborationAPI:
    """Fasad read-only / proposal-only untuk Collaboration & Compatibility.

    Seluruh metode hanya menghasilkan PROPOSAL, PENILAIAN, atau EKSPLANASI.
    Tidak ada mutation kolaborasi, lifecycle, runtime, governance, foundation.
    """

    def __init__(self, registry, descriptors: Optional[Tuple] = None,
                 healths: Optional[Dict[str, str]] = None):
        self._registry = registry
        self._descriptors = tuple(descriptors or ())
        self._healths = dict(healths or {})
        self._proposer = CollaborationProposalEngine(registry)
        self._analyzer = CompatibilityAnalyzer()
        self._resolver = ContractResolutionEngine(registry, self._descriptors)
        self._depchecker = DependencyCompatibilityChecker()
        self._explainer = CollaborationExplainer()

    # --- proposal (WP-12) ---

    def propose(self, origin_identity_id: str,
                needed_capabilities: Sequence[str]) -> Tuple[CollaborationProposal, ...]:
        """Usulkan kolaborasi untuk origin berdasarkan kebutuhan capability."""
        return self._proposer.propose(origin_identity_id,
                                      needed_capabilities,
                                      descriptors=self._descriptors)

    # --- compatibility (WP-13, WP-16) ---

    def compatibility(self, source_identity_id: str, target_identity_id: str,
                      required_contracts: Tuple[str, ...] = ()) -> CompatibilityReport:
        """Laporan kompatibilitas source -> target."""
        c_src = self._contracts_of(source_identity_id)
        c_tgt = self._contracts_of(target_identity_id)
        caps_src = self._capabilities_of(source_identity_id)
        caps_tgt = self._capabilities_of(target_identity_id)
        return self._analyzer.build_report(
            source_identity_id, target_identity_id,
            c_src, c_tgt, caps_src, caps_tgt,
            required_contracts=tuple(required_contracts))

    def explain_compatibility(self, report: CompatibilityReport) -> CollaborationExplanation:
        return self._explainer.explain_compatibility(report)

    # --- contract resolution (WP-14) ---

    def resolve_contract(self, contract: str, capability: str = "",
                         input_schema: str = "",
                         healthy_only: bool = False) -> Tuple[ContractResolution, ...]:
        """Resolusi contract-driven: citizen mana yang memenuhi kebutuhan."""
        req = ResolutionRequirement(contract=contract, capability=capability,
                                    input_schema=input_schema)
        return self._resolver.resolve(req, healthy_only=healthy_only,
                                      healths=self._healths)

    # --- dependency (WP-15) ---

    def analyze_dependency(self, identity_ids: Sequence[str]) -> DependencyAnalysis:
        """Analisis dependency & konflik di antara sekumpulan citizen."""
        contracts_by_id = {cid: self._contracts_of(cid) for cid in identity_ids}
        return self._depchecker.analyze(identity_ids,
                                        contracts_by_id=contracts_by_id,
                                        registry=self._registry)

    # --- explainability (WP-16) ---

    def explain_collaboration(self, spec: CollaborationSpec,
                              reason: str = "") -> CollaborationExplanation:
        return self._explainer.explain_collaboration(spec, reason)

    # --- summary (read-only) ---

    def summarize_spec(self, spec: CollaborationSpec) -> CollaborationSummary:
        from sam.citizen.collaboration.models import is_privilege_free
        return CollaborationSummary(
            collaboration_id=spec.collaboration_id,
            participants=spec.citizen_ids,
            shared_capabilities=spec.shared_capabilities,
            privilege_free=is_privilege_free(spec),
        )

    # --- helpers ---

    def _contracts_of(self, identity_id: str) -> Tuple[str, ...]:
        for d in self._descriptors:
            if getattr(d, "identity_id", None) == identity_id:
                return tuple(getattr(d, "contracts", ()))
        return ()

    def _capabilities_of(self, identity_id: str) -> Tuple[str, ...]:
        for d in self._descriptors:
            if getattr(d, "identity_id", None) == identity_id:
                return tuple(getattr(d, "capabilities", ()))
        return ()
