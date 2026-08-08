# Citizen Collaboration & Compatibility - WP-11..16
# IP-3.3-002 (AO-3.3-001 / ED-3.3-001 2nd cylce)
#
# Model hubungan & kolaborasi antar-Citizen TANPA privilege, plus verifikasi
# kompatibilitas capability & contract, resolusi contract-driven interaction,
# dan analisis dependency.
#
# Guardrails IP-3.3-002 (tetap dipertahankan di seluruh modul):
#   Collaboration != Orchestration
#   Compatibility != Authority
#   Contract Resolution != Execution
#   Proposal != Decision
#   Discovery tetap Registry-based
#   Citizen Equality mutlak; no privileged; no implicit collaboration;
#   no mutation Runtime/Governance/Foundation.

from sam.citizen.collaboration.models import (
    CollaborationChannel,
    CollaborationRole,
    CollaborationSpec,
    CollaborationLink,
    is_privilege_free,
)
from sam.citizen.collaboration.proposal import (
    CollaborationProposal,
    CollaborationProposalEngine,
)
from sam.citizen.collaboration.compatibility import (
    CompatibilityReport,
    CompatibilityVerdict,
    CompatibilityAnalyzer,
)
from sam.citizen.collaboration.contract_resolution import (
    ContractResolution,
    ContractResolutionEngine,
    ResolutionRequirement,
)
from sam.citizen.collaboration.dependency import (
    DependencyConflict,
    DependencyAnalysis,
    DependencyCompatibilityChecker,
)
from sam.citizen.collaboration.explainability import (
    CollaborationExplainer,
    CollaborationExplanation,
)

__all__ = [
    "CollaborationChannel", "CollaborationRole", "CollaborationSpec",
    "CollaborationLink", "is_privilege_free",
    "CollaborationProposal", "CollaborationProposalEngine",
    "CompatibilityReport", "CompatibilityVerdict", "CompatibilityAnalyzer",
    "ContractResolution", "ContractResolutionEngine", "ResolutionRequirement",
    "DependencyConflict", "DependencyAnalysis", "DependencyCompatibilityChecker",
    "CollaborationExplainer", "CollaborationExplanation",
]
