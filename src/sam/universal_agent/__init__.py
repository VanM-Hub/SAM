"""Universal Agent Integration - MISSION-5.3.

Mengintegrasikan berbagai Agent eksternal sebagai Citizen sehingga platform
mampu meng-govern kolaborasi Agent secara konsisten tanpa menjadikan Agent
sebagai bagian internal SAM.

IP-5.3-001: Universal Agent Foundation.
IP-5.3-002: Agent Contract Framework.
IP-5.3-003: Agent Collaboration.
IP-5.3-004: Agent Operational Workspace.
IP-5.3-005: Agent Certification.
"""
from __future__ import annotations

# IP-5.3-001 - Foundation
from .agent_identity import AgentIdentity, AgentStatus, AgentType
from .agent_foundation import (
    AgentCapability,
    AgentCapabilityKind,
    AgentContract,
    AgentDescriptor,
    AgentDiscovery,
    AgentDiscoveryResult,
    AgentHealth,
    AgentHealthCheck,
    AgentHealthState,
    AgentRegistry,
    AgentRegistryEntry,
)
from .agent_lifecycle_api import (
    AgentAPI,
    AgentComplianceChecker,
    AgentComplianceResult,
    AgentLifecycle,
    AgentLifecycleManager,
    AgentLifecycleState,
)

# IP-5.3-002 - Contract Framework
from .agent_contract_framework import (
    AgentCapabilityResolution,
    AgentCapabilityResolver,
    AgentContext,
    AgentContractComplianceChecker,
    AgentContractComplianceResult,
    AgentExplanation,
    AgentInteractionContract,
    AgentRequest,
    AgentResponse,
    AgentResultState,
    AgentSession,
    InteropCheck,
    InteroperabilityChecker,
    InteroperabilityState,
    SessionState,
)

# IP-5.3-003 - Collaboration
from .agent_collaboration import (
    CollaborationComplianceChecker,
    CollaborationComplianceResult,
    CollaborationManager,
    CollaborationProposal,
    CollaborationRecord,
    CollaborationState,
    NegotiationResult,
)

# IP-5.3-004/005 - Workspace & Certification
from .agent_workspace_cert import (
    AgentCertEvidence,
    AgentCertification,
    AgentCertStatus,
    AgentExplorer,
    AgentInfo,
    AgentInvestigation,
    AgentWorkspace,
)

__all__ = [
    "AgentIdentity", "AgentStatus", "AgentType",
    "AgentCapability", "AgentCapabilityKind", "AgentContract", "AgentDescriptor",
    "AgentDiscovery", "AgentDiscoveryResult", "AgentHealth", "AgentHealthCheck",
    "AgentHealthState", "AgentRegistry", "AgentRegistryEntry",
    "AgentAPI", "AgentComplianceChecker", "AgentComplianceResult",
    "AgentLifecycle", "AgentLifecycleManager", "AgentLifecycleState",
    "AgentCapabilityResolution", "AgentCapabilityResolver", "AgentContext",
    "AgentContractComplianceChecker", "AgentContractComplianceResult",
    "AgentExplanation", "AgentInteractionContract", "AgentRequest", "AgentResponse",
    "AgentResultState", "AgentSession", "InteropCheck", "InteroperabilityChecker",
    "InteroperabilityState", "SessionState",
    "CollaborationComplianceChecker", "CollaborationComplianceResult",
    "CollaborationManager", "CollaborationProposal", "CollaborationRecord",
    "CollaborationState", "NegotiationResult",
    "AgentCertEvidence", "AgentCertification", "AgentCertStatus",
    "AgentExplorer", "AgentInfo", "AgentInvestigation", "AgentWorkspace",
]
