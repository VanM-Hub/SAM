"""Universal Connector Runtime — Phase XI.

Subsystem mandiri untuk komunikasi SAM dengan sistem eksternal secara
provider-agnostic, preview-only, dan tanpa implementasi provider.
"""
from .connector_descriptor import (
    ConnectorDescriptor, ConnectorStatus, ConnectorSummary,
)
from .connector_capability import ConnectorCapability, CapabilityKind
from .connector_contract import ConnectorContract, ContractCompliance
from .connector_metadata import ConnectorMetadata
from .connector_registry import (
    ConnectorRegistry, ConnectorRegistrationResult,
)
from .conversation_connector import ConversationConnectorBridge
from .dashboard_connector import DashboardConnectorBridge, ExecutionCard
from .connector_discovery import DiscoveryResult, DiscoveryReport
from .connector_locator import ConnectorLocator
from .connector_catalog import ConnectorCatalog
from .connector_filter import ConnectorFilter
from .connector_validator import ConnectorValidator, ValidationIssue, ValidationReport
from .conversation_discovery import ConversationDiscoveryBridge
from .dashboard_discovery import DashboardDiscoveryBridge
from .capability_profile import CapabilityProfile
from .capability_matrix import CapabilityMatrixEntry, CapabilityMatrix, CapabilityMatrixBuilder
from .capability_validator import CapabilityValidator, CapabilityValidationIssue, CapabilityValidationReport
from .capability_selector import CapabilitySelector, CapabilitySelection
from .capability_report import CapabilityReport, CapabilityReporter
from .conversation_capability import ConversationCapabilityBridge
from .dashboard_capability import DashboardCapabilityBridge
from .binding_request import BindingRequest
from .binding_result import BindingResult
from .binding_registry import BindingRegistry
from .binding_validator import BindingValidator, BindingValidationReport
from .binding_history import BindingHistory, BindingHistoryEntry
from .conversation_binding import ConversationBindingBridge
from .dashboard_binding import DashboardBindingBridge
from .session_context import SessionContext
from .connector_session import ConnectorSessionManager
from .session_registry import SessionRegistry
from .session_snapshot import SessionSnapshot
from .session_summary import SessionSummary, SessionSummarizer
from .conversation_session import ConversationSessionBridge
from .dashboard_session import DashboardSessionBridge
from .connector_router import ConnectorRouter, RoutingPolicy, RoutingResult
from .routing_validator import RoutingValidator, RoutingValidationReport
from .routing_summary import RoutingSummary, RoutingSummarizer
from .conversation_routing import ConversationRoutingBridge
from .dashboard_routing import DashboardRoutingBridge
from .translation_request import TranslationRequest
from .translation_result import TranslationResult
from .translation_engine import TranslationEngine
from .translation_validator import TranslationValidator, TranslationValidationReport
from .translation_summary import TranslationSummary, TranslationSummarizer
from .conversation_translation import ConversationTranslationBridge
from .dashboard_translation import DashboardTranslationBridge
from .preview_request import PreviewRequest
from .preview_result import PreviewResult
from .preview_validator import PreviewValidator, PreviewValidationReport
from .preview_engine import PreviewEngine
from .preview_report import PreviewReport, PreviewReporter
from .preview_history import PreviewHistory, PreviewHistoryEntry
from .conversation_preview import ConversationPreviewBridge
from .dashboard_preview import DashboardPreviewBridge
from .connector_metrics import ConnectorMetrics
from .connector_health import ConnectorHealth, ConnectorHealthChecker
from .connector_statistics import ConnectorStatistics, ConnectorStatisticsCollector
from .connector_snapshot import ConnectorSnapshot
from .connector_history import ConnectorHistory
from .conversation_monitor import ConversationMonitorBridge
from .dashboard_monitor import DashboardMonitorBridge
from .runtime import RuntimeCheck, RuntimeReadiness, ConnectorRuntime
from .runtime_pipeline import PipelineStage, RuntimePipeline, RuntimePipelineBuilder
from .runtime_coordinator import CoordinationResult, RuntimeCoordinator
from .runtime_status import RuntimeStatus
from .runtime_report import RuntimeReport, RuntimeReporter
from .conversation_runtime import ConversationRuntimeBridge
from .dashboard_runtime import DashboardRuntimeBridge
from .connector_certification import CertificationCriterion, CertificationResult, ConnectorCertifier
from .connector_score import ConnectorScore, ConnectorScorer
from .certification_validator import CertificationValidation, CertificationValidator
from .connector_report import ConnectorReport, ConnectorReporter
from .connector_manifest import ConnectorManifest
from .conversation_certification import ConversationCertificationBridge
from .dashboard_certification import DashboardCertificationBridge

__all__ = [
    "ConnectorDescriptor", "ConnectorStatus", "ConnectorSummary",
    "ConnectorCapability", "CapabilityKind",
    "ConnectorContract", "ContractCompliance",
    "ConnectorMetadata",
    "ConnectorRegistry", "ConnectorRegistrationResult",
    "ConversationConnectorBridge",
    "DashboardConnectorBridge", "ExecutionCard",
    "DiscoveryResult", "DiscoveryReport",
    "ConnectorLocator", "ConnectorCatalog", "ConnectorFilter",
    "ConnectorValidator", "ValidationIssue", "ValidationReport",
    "ConversationDiscoveryBridge", "DashboardDiscoveryBridge",
    "CapabilityProfile",
    "CapabilityMatrixEntry", "CapabilityMatrix", "CapabilityMatrixBuilder",
    "CapabilityValidator", "CapabilityValidationIssue", "CapabilityValidationReport",
    "CapabilitySelector", "CapabilitySelection",
    "CapabilityReport", "CapabilityReporter",
    "ConversationCapabilityBridge", "DashboardCapabilityBridge",
    "BindingRequest", "BindingResult", "BindingRegistry",
    "BindingValidator", "BindingValidationReport",
    "BindingHistory", "BindingHistoryEntry",
    "ConversationBindingBridge", "DashboardBindingBridge",
    "SessionContext", "ConnectorSessionManager",
    "SessionRegistry", "SessionSnapshot",
    "SessionSummary", "SessionSummarizer",
    "ConversationSessionBridge", "DashboardSessionBridge",
    "ConnectorRouter", "RoutingPolicy", "RoutingResult",
    "RoutingValidator", "RoutingValidationReport",
    "RoutingSummary", "RoutingSummarizer",
    "ConversationRoutingBridge", "DashboardRoutingBridge",
    "TranslationRequest", "TranslationResult", "TranslationEngine",
    "TranslationValidator", "TranslationValidationReport",
    "TranslationSummary", "TranslationSummarizer",
    "ConversationTranslationBridge", "DashboardTranslationBridge",
    "PreviewRequest", "PreviewResult", "PreviewValidator", "PreviewValidationReport",
    "PreviewEngine", "PreviewReport", "PreviewReporter",
    "PreviewHistory", "PreviewHistoryEntry",
    "ConversationPreviewBridge", "DashboardPreviewBridge",
    "ConnectorMetrics", "ConnectorHealth", "ConnectorHealthChecker",
    "ConnectorStatistics", "ConnectorStatisticsCollector",
    "ConnectorSnapshot", "ConnectorHistory",
    "ConversationMonitorBridge", "DashboardMonitorBridge",
    "RuntimeCheck", "RuntimeReadiness", "ConnectorRuntime",
    "PipelineStage", "RuntimePipeline", "RuntimePipelineBuilder",
    "CoordinationResult", "RuntimeCoordinator",
    "RuntimeStatus", "RuntimeReport", "RuntimeReporter",
    "ConversationRuntimeBridge", "DashboardRuntimeBridge",
    "CertificationCriterion", "CertificationResult", "ConnectorCertifier",
    "ConnectorScore", "ConnectorScorer",
    "CertificationValidation", "CertificationValidator",
    "ConnectorReport", "ConnectorReporter",
    "ConnectorManifest",
    "ConversationCertificationBridge", "DashboardCertificationBridge",
]
