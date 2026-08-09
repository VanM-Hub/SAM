"""Execution Runtime - Execution Runtime v26.0.0.

Program C - Real Execution Runtime + Program G - Execution Evolution +
IP-4.1-001 Provider Execution Foundation.

Execution Foundation, Request/Response, Approval, Dispatcher, Engine,
Rollback, Monitoring, Safety, Certification, Integration, Provider Activation,
Simulation Capability (evidence deterministik untuk approval/audit).

IP-4.1-001 menambah: Credential Management & Verification, Execution Session,
Provider Connection, Execution Context.
"""

from .simulation_evidence import SimulationEvidence
from .simulation_engine import SimulationEngine, SimulationReport
from .simulation_integration import SimulationIntegration, SimulatedExecutionReport

# IP-4.1-001 - Provider Execution Foundation
from .credential import (
    CredentialStatus,
    CredentialSource,
    CredentialReference,
    CredentialStatusResult,
    CredentialAuditRecord,
    CredentialSummary,
    ExecutionCredentialManager,
    mask_secret,
    CREDENTIAL_REFERENCES,
)
from .credential_verifier import (
    VerificationCheck,
    CredentialVerification,
    VerificationSummary,
    CredentialVerifier,
)
from .execution_session import (
    SessionState,
    SessionMetadata,
    SessionContext,
    SessionEvent,
    ExecutionSession,
    ExecutionSessionManager,
    deterministic_session_id,
)
from .provider_connection import (
    ProviderIdentity,
    ConnectionHealth,
    ConnectionCheck,
    ProviderConnection,
    ProviderConnectionManager,
    PROVIDER_BASE_URLS,
)
from .execution_context_manager import (
    GovernanceContext,
    MissionContext,
    WorkflowContext,
    RuntimeContext,
    ProviderContext,
    ExecutionContext,
    ExecutionContextBuilder,
)

# IP-4.1-001 - Request/Response Serializer (WP-06/07)
from .execution_serializer import (
    ExecutionRequestSerializer,
    ExecutionResponseSerializer,
    ExecutionSerializationError,
    VALID_MODES,
    VALID_STATUS,
)
# IP-4.1-001 - Execution Audit (WP-08)
from .execution_audit import (
    AuditTimelineStep,
    ExecutionAuditRecord,
    AuditSummary,
    ExecutionAudit,
    audit_hash,
)
# IP-4.1-001 - Execution Compliance (WP-09)
from .execution_compliance import (
    ComplianceCheck,
    ExecutionCompliance,
    GovernedExecutionInvariant,
    ExecutionComplianceChecker,
)

# IP-4.1-002 - Governed Execution (WP-11..17)
from .execution_explainer import (
    RationaleStep,
    ExecutionExplanation,
    ExecutionExplainer,
)
from .execution_verification import (
    VerificationCriterion,
    ExecutionVerification,
    ExecutionVerifier,
)
from .governed_execution import (
    ExecutionEvidence,
    GovernedExecutionResult,
    GovernedExecution,
)
from .execution_api import (
    ExecutionAPIStatus,
    ExecutionAPI,
)

__all__ = [
    # Program C + G (existing)
    "SimulationEvidence",
    "SimulationEngine",
    "SimulationReport",
    "SimulationIntegration",
    "SimulatedExecutionReport",
    # IP-4.1-001 - Credential Management (WP-01)
    "CredentialStatus",
    "CredentialSource",
    "CredentialReference",
    "CredentialStatusResult",
    "CredentialAuditRecord",
    "CredentialSummary",
    "ExecutionCredentialManager",
    "mask_secret",
    "CREDENTIAL_REFERENCES",
    # IP-4.1-001 - Credential Verification (WP-02)
    "VerificationCheck",
    "CredentialVerification",
    "VerificationSummary",
    "CredentialVerifier",
    # IP-4.1-001 - Execution Session (WP-03)
    "SessionState",
    "SessionMetadata",
    "SessionContext",
    "SessionEvent",
    "ExecutionSession",
    "ExecutionSessionManager",
    "deterministic_session_id",
    # IP-4.1-001 - Provider Connection (WP-04)
    "ProviderIdentity",
    "ConnectionHealth",
    "ConnectionCheck",
    "ProviderConnection",
    "ProviderConnectionManager",
    "PROVIDER_BASE_URLS",
    # IP-4.1-001 - Execution Context (WP-05)
    "GovernanceContext",
    "MissionContext",
    "WorkflowContext",
    "RuntimeContext",
    "ProviderContext",
    "ExecutionContext",
    "ExecutionContextBuilder",
    # IP-4.1-001 - Request/Response Serializer (WP-06/07)
    "ExecutionRequestSerializer",
    "ExecutionResponseSerializer",
    "ExecutionSerializationError",
    "VALID_MODES",
    "VALID_STATUS",
    # IP-4.1-001 - Execution Audit (WP-08)
    "AuditTimelineStep",
    "ExecutionAuditRecord",
    "AuditSummary",
    "ExecutionAudit",
    "audit_hash",
    # IP-4.1-001 - Execution Compliance (WP-09)
    "ComplianceCheck",
    "ExecutionCompliance",
    "GovernedExecutionInvariant",
    "ExecutionComplianceChecker",
    # IP-4.1-002 - Governed Execution (WP-11..17)
    "RationaleStep",
    "ExecutionExplanation",
    "ExecutionExplainer",
    "VerificationCriterion",
    "ExecutionVerification",
    "ExecutionVerifier",
    "ExecutionEvidence",
    "GovernedExecutionResult",
    "GovernedExecution",
    "ExecutionAPIStatus",
    "ExecutionAPI",
]
