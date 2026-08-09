"""Universal AI Integration - MISSION-5.1.

Mengintegrasikan berbagai Artificial Intelligence Provider ke dalam Governance
Platform melalui Provider Contract yang seragam (provider-agnostic,
credential-safe, governed, auditable).

IP-5.1-001: Universal AI Provider Foundation.
IP-5.1-002: Multi Provider Integration.
IP-5.1-003: AI Conversation Platform.
IP-5.1-004: Reasoning & Context Management.
IP-5.1-005: AI Certification.
"""
from __future__ import annotations

# IP-5.1-001 - Foundation
from .provider_identity import (
    ProviderIdentity,
    ProviderStatus,
    ProviderType,
)
from .provider_registry import AIProviderRegistry, RegistryEntry
from .provider_descriptor import (
    AIModelDescriptor,
    ModelCapability,
    ProviderDescriptor,
)
from .capability_model import AICapability, AICapabilityKind, AICapabilityModel
from .provider_discovery import AIProviderDiscovery, DiscoveryResult
from .provider_health import AIProviderHealthCheck, HealthEvidence, HealthState, ProviderHealth
from .provider_api import AIProviderAPI
from .ai_provider_compliance import (
    AIProviderComplianceChecker,
    AIProviderComplianceResult,
)

# IP-5.1-002 - Multi Provider Integration
from .adapter_framework import (
    ConnectionStatus,
    NormalizedResponse,
    ProviderAdapter,
    ProviderAdapterError,
    ProviderRequest,
)
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .google_adapter import GoogleAIAdapter
from .local_model_adapter import LocalModelAdapter
from .capability_resolution import (
    CapabilityMapping,
    CapabilityResolver,
    ResolvedCapability,
)
from .provider_selection import (
    ProviderResolution,
    ProviderSelector,
    SelectionEvidence,
)
from .failover_assessment import FailoverAssessor, FailoverAssessment, FailoverCandidate
from .provider_integration_compliance import (
    ProviderIntegrationComplianceChecker,
    ProviderIntegrationComplianceResult,
)

# IP-5.1-003 - Conversation Platform
from .conversation_model import Conversation, ConversationStatus
from .conversation_session import ConversationSession, SessionManager, SessionState
from .message_model import Message, MessageRole
from .context_assembly import AssembledContext, ContextAssembler
from .provider_invocation import InvocationResult, ProviderInvoker
from .response_normalization import (
    NormalizedConversationResponse,
    ResponseNormalizer,
)
from .conversation_history import ConversationHistoryStore, HistoryPage
from .conversation_api import ConversationAPI
from .conversation_compliance import (
    ConversationComplianceChecker,
    ConversationComplianceResult,
)

# IP-5.1-004 - Reasoning & Context Management
from .reasoning_context_model import ReasoningContext
from .evidence_context import EvidenceContextEntry, EvidenceContextProvider
from .operational_context import OperationalContext, OperationalContextProvider
from .experience_context import ExperienceContextProvider, ExperienceEntry
from .context_resolution import (
    ContextResolutionEngine,
    MissingInfo,
    ResolvedReasoningContext,
)
from .reasoning_request import ReasoningRequest
from .reasoning_response import ReasoningResponse
from .reasoning_explainability import ReasoningExplanation, ReasoningExplainer
from .reasoning_compliance import (
    ReasoningComplianceChecker,
    ReasoningComplianceResult,
)

# IP-5.1-005 - AI Certification
from .ai_certification import (
    AICertification,
    CertificationEvidence,
    CertificationResult,
    CertStatus,
    VerificationArea,
)

__all__ = [
    # Foundation
    "ProviderIdentity", "ProviderStatus", "ProviderType",
    "AIProviderRegistry", "RegistryEntry",
    "AIModelDescriptor", "ModelCapability", "ProviderDescriptor",
    "AICapability", "AICapabilityKind", "AICapabilityModel",
    "AIProviderDiscovery", "DiscoveryResult",
    "AIProviderHealthCheck", "HealthEvidence", "HealthState", "ProviderHealth",
    "AIProviderAPI",
    "AIProviderComplianceChecker", "AIProviderComplianceResult",
    # Multi Provider
    "ConnectionStatus", "NormalizedResponse", "ProviderAdapter", "ProviderAdapterError", "ProviderRequest",
    "OpenAIAdapter", "AnthropicAdapter", "GoogleAIAdapter", "LocalModelAdapter",
    "CapabilityMapping", "CapabilityResolver", "ResolvedCapability",
    "ProviderResolution", "ProviderSelector", "SelectionEvidence",
    "FailoverAssessor", "FailoverAssessment", "FailoverCandidate",
    "ProviderIntegrationComplianceChecker", "ProviderIntegrationComplianceResult",
    # Conversation
    "Conversation", "ConversationStatus",
    "ConversationSession", "SessionManager", "SessionState",
    "Message", "MessageRole",
    "AssembledContext", "ContextAssembler",
    "InvocationResult", "ProviderInvoker",
    "NormalizedConversationResponse", "ResponseNormalizer",
    "ConversationHistoryStore", "HistoryPage",
    "ConversationAPI",
    "ConversationComplianceChecker", "ConversationComplianceResult",
    # Reasoning
    "ReasoningContext",
    "EvidenceContextEntry", "EvidenceContextProvider",
    "OperationalContext", "OperationalContextProvider",
    "ExperienceContextProvider", "ExperienceEntry",
    "ContextResolutionEngine", "MissingInfo", "ResolvedReasoningContext",
    "ReasoningRequest", "ReasoningResponse",
    "ReasoningExplanation", "ReasoningExplainer",
    "ReasoningComplianceChecker", "ReasoningComplianceResult",
    # Certification
    "AICertification", "CertificationEvidence", "CertificationResult", "CertStatus", "VerificationArea",
]
