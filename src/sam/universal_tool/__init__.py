"""Universal Tool Integration - MISSION-5.2.

Mengintegrasikan berbagai Tool operasional sebagai Citizen sehingga dapat
di-govern secara konsisten melalui Tool Contract tanpa vendor lock-in.

IP-5.2-001: Universal Tool Foundation.
IP-5.2-002: Tool Connector Framework.
IP-5.2-003: Governed Tool Execution / Tool Capability Integration.
IP-5.2-004: Operational Tool Workspace.
IP-5.2-005: Tool Ecosystem Certification.
"""
from __future__ import annotations

# IP-5.2-001 - Tool Foundation
from .tool_identity import ToolIdentity, ToolStatus, ToolType
from .tool_registry import ToolRegistry, ToolRegistryEntry
from .tool_descriptor import ToolCapability, ToolCapabilityKind, ToolDescriptor
from .tool_contract import ToolContract
from .tool_discovery import ToolDiscovery, ToolDiscoveryResult
from .tool_health import ToolHealth, ToolHealthCheck, ToolHealthState
from .tool_api import ToolAPI
from .tool_compliance import ToolComplianceChecker, ToolComplianceResult

# IP-5.2-002 - Connector Framework
from .connector_model import (
    ConnectorHandle,
    ConnectorState,
    ConnectorType,
    ToolConnector,
)
from .connector_registry import ConnectorRegistry
from .connector_lifecycle import ConnectorLifecycle
from .connection_management import (
    ConnectionManager,
    ConnectionRecord,
    ConnectionState,
    CredentialBinder,
    CredentialBinding,
)
from .capability_binding import CapabilityBinder, CapabilityBinding
from .connector_health import ConnectorHealth, ConnectorHealthCheck, ConnectorHealthState
from .connector_api import ConnectorAPI, ConnectorView
from .connector_compliance import ConnectorComplianceChecker, ConnectorComplianceResult

# IP-5.2-003 - Governed Tool Execution
from .capability_resolution import ToolCapabilityResolution, ToolCapabilityResolver
from .tool_request import ToolRequest
from .governed_tool_invocation import (
    ExecutionStage,
    GovernanceDecision,
    GovernedToolInvoker,
    ToolExecutionContext,
)
from .tool_response import ToolResponse, ToolResultState, ToolResultVerifier
from .tool_audit import ToolAuditEntry, ToolAuditLog, ToolExplainer
from .tool_execution_compliance import (
    ToolExecutionComplianceChecker,
    ToolExecutionComplianceResult,
)

# IP-5.2-004 - Operational Tool Workspace
from .tool_explorer import CapabilityInfo, ToolExplorer, ToolInfo
from .tool_workspace import (
    ToolConnectionStatus,
    ToolConnectionStatusView,
    ToolInvestigation,
    ToolOperationalContext,
    ToolWorkspace,
)

# IP-5.2-005 - Tool Certification
from .tool_certification import (
    ToolCertification,
    ToolCertificationEvidence,
    ToolCertificationResult,
    ToolCertStatus,
    WorkspaceComplianceChecker,
    WorkspaceComplianceResult,
)

__all__ = [
    "ToolIdentity", "ToolStatus", "ToolType",
    "ToolRegistry", "ToolRegistryEntry",
    "ToolCapability", "ToolCapabilityKind", "ToolDescriptor",
    "ToolContract",
    "ToolDiscovery", "ToolDiscoveryResult",
    "ToolHealth", "ToolHealthCheck", "ToolHealthState",
    "ToolAPI",
    "ToolComplianceChecker", "ToolComplianceResult",
    "ConnectorHandle", "ConnectorState", "ConnectorType", "ToolConnector",
    "ConnectorRegistry", "ConnectorLifecycle",
    "ConnectionManager", "ConnectionRecord", "ConnectionState",
    "CredentialBinder", "CredentialBinding",
    "CapabilityBinder", "CapabilityBinding",
    "ConnectorHealth", "ConnectorHealthCheck", "ConnectorHealthState",
    "ConnectorAPI", "ConnectorView",
    "ConnectorComplianceChecker", "ConnectorComplianceResult",
    "ToolCapabilityResolution", "ToolCapabilityResolver",
    "ToolRequest",
    "ExecutionStage", "GovernanceDecision", "GovernedToolInvoker", "ToolExecutionContext",
    "ToolResponse", "ToolResultState", "ToolResultVerifier",
    "ToolAuditEntry", "ToolAuditLog", "ToolExplainer",
    "ToolExecutionComplianceChecker", "ToolExecutionComplianceResult",
    "CapabilityInfo", "ToolExplorer", "ToolInfo",
    "ToolConnectionStatus", "ToolConnectionStatusView", "ToolInvestigation",
    "ToolOperationalContext", "ToolWorkspace",
    "ToolCertification", "ToolCertificationEvidence", "ToolCertificationResult",
    "ToolCertStatus", "WorkspaceComplianceChecker", "WorkspaceComplianceResult",
]
