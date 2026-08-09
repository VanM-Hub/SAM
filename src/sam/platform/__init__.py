# Platform Experience - MISSION-3.5 (IP-3.5-001 Platform Workspace
#                + IP-3.5-002 Mission Experience
#                + IP-3.5-003 Citizen Experience
#                + IP-3.5-004 Explainability Experience
#                + IP-3.5-005 Platform Integration)
# AO-ENG-001 / Work Order MISSION-3.5 (2026-08-09, Engineering Started)
#
# Bounded context baru: src/sam/platform/ (KEPUTUSAN Option B, 2026-08-09).
# MISSION-3.5 TIDAK menambah governance/runtime/citizen/federation/authority.
# Ia MENYATUKAN seluruh capability yang sudah ada (SAM 2.x -> 3.4) menjadi
# satu pengalaman platform yang konsisten.
#
# Consumer-only: platform/ MENGONSUMSI capability yang ada via API publik /
# subpackage; TIDAK memodifikasi governance/runtime/citizen/federation,
# TIDAK mengubah authority.
# presentation/ tetap delivery/UI layer dan MENGONSUMSI platform/ (bukan
# tempat implementasi domain Platform Experience).
#
# Prinsip (roadmap SAM 3.5 - Platform Experience):
#   Powerful platform becomes usable platform.
#   Platform Experience presents governance. It never performs governance.
#   Presentation over implementation; Observation over intervention;
#   Visualization over orchestration; Explanation over abstraction;
#   Trust through transparency.
#
# Batas arsitektural platform/ (presentation-passive):
#   platform/ SHALL NOT: perform governance, perform approval, perform
#   execution, coordinate runtime, modify citizens, bypass runtime service,
#   create new authority, AI-controlled operation, distributed execution.
#   platform/ MENGONSUMSI & MENYAJIKAN; never performs.
#
# IP-3.5-001 (Platform Workspace) - Guardrail PEX-01..10 (compliance.py):
#   Workspace != Governance; Navigation != Execution; Perspective != Authority;
#   Context != State Control; Layout != Orchestration;
#   Descriptor != Contract Execution; View != Intervention;
#   Presentation Passive; Consumer-only; Read-only API.
#
# Version: dimulai 3.5.0 (IP-3.5-001).

# IP-3.5-001 - Platform Workspace (WP-01..08)
from sam.platform.workspace_model import (
    PlatformDomain,
    Perspective,
    PerspectiveBinding,
    WorkspaceModel,
    build_domain,
    build_perspective,
)
from sam.platform.navigation import NavigationModel, NavigationRoute, build_navigation
from sam.platform.perspective import PerspectiveRegistry, PerspectiveState
from sam.platform.context import WorkspaceContext, ContextStore
from sam.platform.layout import LayoutModel, PanelSlot
from sam.platform.descriptor import WorkspaceDescriptor, descriptor_from_model
from sam.platform.workspace_api import WorkspaceAPI, WorkspaceSnapshot, default_workspace
from sam.platform.compliance import ComplianceResult, compliance_check

# IP-3.5-002 - Mission Experience (WP-09..16)
from sam.platform.mission_workspace import (
    MissionInput,
    MissionTimelineInput,
    MissionHealthInput,
    MissionJourney,
    MissionJourneyStep,
    MissionWorkspaceView,
    build_journey,
)
from sam.platform.mission_timeline import (
    MissionTimelineView,
    MissionProgress,
    compute_progress,
    timeline_from_checkpoints,
)
from sam.platform.mission_context import (
    MissionContext,
    MissionInsight,
    build_insight,
)
from sam.platform.mission_api import MissionAPI, MissionSnapshot
from sam.platform.compliance import mission_compliance_check

# IP-3.5-003 - Citizen Experience (WP-17..23)
from sam.platform.citizen_workspace import (
    CitizenInput,
    FederationInput,
    FederationMemberInput,
    CitizenWorkspaceView,
    FederationWorkspaceView,
    build_citizen_view,
    build_federation_view,
)
from sam.platform.collaboration_workspace import (
    CollaborationInput,
    CollaborationWorkspaceView,
    CompatibilityAssessment,
    CertificationStatus,
    CertificationWorkspaceView,
    assess_compatibility,
    build_certification_view,
)
from sam.platform.citizen_api import CitizenSnapshot, CitizenExperienceAPI
from sam.platform.compliance import citizen_compliance_check

# IP-3.5-004 - Explainability Experience (WP-24..28)
from sam.platform.evidence_graph import (
    EvidenceAggregate,
    EvidenceGraph,
    EvidenceInput,
    EvidenceLink,
    EvidenceNode,
    aggregate_evidence,
    build_evidence_graph,
)
from sam.platform.explainability import (
    DomainPairCoverage,
    ExplainabilitySummary,
    explain_graph,
)
from sam.platform.evidence_chain import EvidenceChain, build_chain, orphaned_evidence
from sam.platform.explain_api import (
    ExplainabilityAPI,
    ExplainabilitySnapshot,
)
from sam.platform.compliance import explainability_compliance_check

# IP-3.6-A - Production Governance (Track A, WP-A1..A5)
from sam.platform.production_governance import (
    BaselineEntry,
    BaselineVerification,
    ComplianceCheckItem,
    GovernanceProfile,
    GovernanceProfileStatus,
    GovernanceReadiness,
    PolicyEntry,
    PolicyValidationResult,
    ReadinessInput,
    assess_governance_profile,
    assess_readiness,
    operational_compliance_score,
    validate_operational_policies,
    verify_governance_baseline,
)
from sam.platform.compliance import production_governance_compliance_check

# IP-3.6-B - Platform Operations (Track B, WP-B1..B5)
from sam.platform.platform_operations import (
    ConfigSetting,
    ConfigVerification,
    DeploymentArtifact,
    DeploymentValidation,
    EnvironmentFactor,
    EnvironmentValidation,
    ShutdownCheck,
    ShutdownVerification,
    StartupCheck,
    StartupVerification,
    validate_deployment,
    validate_environment,
    verify_configuration,
    verify_shutdown,
    verify_startup,
)
from sam.platform.compliance import platform_operations_compliance_check

# IP-3.6-C - Operational Evidence (Track C, WP-C1..C5)
from sam.platform.operational_evidence import (
    AuditEvent,
    AuditEvidenceSummary,
    GovernanceEvidenceAggregate,
    GovernanceEvidencePoint,
    HealthEvidenceSummary,
    HealthSignal,
    MetricPoint,
    MetricsSummary,
    RuntimeConsolidation,
    RuntimeEvidencePiece,
    aggregate_governance_evidence,
    consolidate_runtime_evidence,
    summarize_audit_evidence,
    summarize_health_evidence,
    summarize_metrics,
)
from sam.platform.compliance import operational_evidence_compliance_check

# IP-3.6-D - Production Reliability (Track D, WP-D1..D5)
from sam.platform.production_reliability import (
    DiagnosticFinding,
    DiagnosticsSummary,
    LongRunningObservation,
    LongRunningVerification,
    RecoveryPlanPiece,
    RecoverabilityValidation,
    ReliabilityObservation,
    ReliabilityVerification,
    StabilityAssessment,
    StabilitySample,
    assess_stability,
    summarize_diagnostics,
    validate_recoverability,
    verify_long_running,
    verify_reliability,
)
from sam.platform.compliance import production_reliability_compliance_check

# IP-3.6-E - Mission Certification (Track E, WP-E1..E5)
from sam.platform.mission_certification import (
    ComplianceGroup,
    ComplianceRegression,
    MissionEngineeringReport,
    MissionReadiness,
    OperationalRegression,
    ProductionCertification,
    ReadinessGate,
    RegressionSuite,
    ReportSection,
    TrackResult,
    assess_mission_readiness,
    build_engineering_report,
    certify_end_to_end,
    run_compliance_regression,
    run_operational_regression,
)
from sam.platform.compliance import mission_certification_compliance_check

# IP-3.5-005 - Platform Integration (WP-29..33)
from sam.platform.integration import (
    PlatformEngine,
    PlatformPresentation,
)
from sam.platform.platform_check import (
    GateResult,
    IntegrationCertification,
    ReadinessAttributes,
    certification_gate,
    compliance_gate,
    production_readiness_check,
    regression_gate,
)

__version__ = "3.5.0"

__all__ = [
    # WP-01 model
    "PlatformDomain",
    "Perspective",
    "PerspectiveBinding",
    "WorkspaceModel",
    "build_domain",
    "build_perspective",
    # WP-02 navigation
    "NavigationModel",
    "NavigationRoute",
    "build_navigation",
    # WP-03 perspective
    "PerspectiveRegistry",
    "PerspectiveState",
    # WP-04 context
    "WorkspaceContext",
    "ContextStore",
    # WP-05 layout
    "LayoutModel",
    "PanelSlot",
    # WP-06 descriptor
    "WorkspaceDescriptor",
    "descriptor_from_model",
    # WP-07 api
    "WorkspaceAPI",
    "WorkspaceSnapshot",
    "default_workspace",
    # WP-08 compliance
    "ComplianceResult",
    "compliance_check",
    # WP-09 mission workspace
    "MissionInput",
    "MissionTimelineInput",
    "MissionHealthInput",
    "MissionJourney",
    "MissionJourneyStep",
    "MissionWorkspaceView",
    "build_journey",
    # WP-10/12 timeline & progress
    "MissionTimelineView",
    "MissionProgress",
    "compute_progress",
    "timeline_from_checkpoints",
    # WP-13/14 context & insight
    "MissionContext",
    "MissionInsight",
    "build_insight",
    # WP-15 mission api
    "MissionAPI",
    "MissionSnapshot",
    # WP-16 mission compliance
    "mission_compliance_check",
    # WP-17 citizen workspace
    "CitizenInput",
    "FederationInput",
    "FederationMemberInput",
    "CitizenWorkspaceView",
    "FederationWorkspaceView",
    "build_citizen_view",
    "build_federation_view",
    # WP-19/20/21 collaboration, compatibility, certification
    "CollaborationInput",
    "CollaborationWorkspaceView",
    "CompatibilityAssessment",
    "CertificationStatus",
    "CertificationWorkspaceView",
    "assess_compatibility",
    "build_certification_view",
    # WP-22 citizen api
    "CitizenSnapshot",
    "CitizenExperienceAPI",
    # WP-23 citizen compliance
    "citizen_compliance_check",
    # WP-24/25 evidence graph & aggregation
    "EvidenceAggregate",
    "EvidenceGraph",
    "EvidenceInput",
    "EvidenceLink",
    "EvidenceNode",
    "aggregate_evidence",
    "build_evidence_graph",
    # WP-26 cross-domain explainability
    "DomainPairCoverage",
    "ExplainabilitySummary",
    "explain_graph",
    # WP-27 evidence chain viewer
    "EvidenceChain",
    "build_chain",
    "orphaned_evidence",
    # WP-28 explainability api
    "ExplainabilityAPI",
    "ExplainabilitySnapshot",
    # WP-28 compliance
    "explainability_compliance_check",
    # IP-3.6-A Production Governance
    "BaselineEntry",
    "BaselineVerification",
    "ComplianceCheckItem",
    "GovernanceProfile",
    "GovernanceProfileStatus",
    "GovernanceReadiness",
    "PolicyEntry",
    "PolicyValidationResult",
    "ReadinessInput",
    "assess_governance_profile",
    "assess_readiness",
    "operational_compliance_score",
    "validate_operational_policies",
    "verify_governance_baseline",
    "production_governance_compliance_check",
    # IP-3.6-B Platform Operations
    "ConfigSetting",
    "ConfigVerification",
    "DeploymentArtifact",
    "DeploymentValidation",
    "EnvironmentFactor",
    "EnvironmentValidation",
    "ShutdownCheck",
    "ShutdownVerification",
    "StartupCheck",
    "StartupVerification",
    "validate_deployment",
    "validate_environment",
    "verify_configuration",
    "verify_shutdown",
    "verify_startup",
    "platform_operations_compliance_check",
    # IP-3.6-C Operational Evidence
    "AuditEvent",
    "AuditEvidenceSummary",
    "GovernanceEvidenceAggregate",
    "GovernanceEvidencePoint",
    "HealthEvidenceSummary",
    "HealthSignal",
    "MetricPoint",
    "MetricsSummary",
    "RuntimeConsolidation",
    "RuntimeEvidencePiece",
    "aggregate_governance_evidence",
    "consolidate_runtime_evidence",
    "summarize_audit_evidence",
    "summarize_health_evidence",
    "summarize_metrics",
    "operational_evidence_compliance_check",
    # IP-3.6-D Production Reliability
    "DiagnosticFinding",
    "DiagnosticsSummary",
    "LongRunningObservation",
    "LongRunningVerification",
    "RecoveryPlanPiece",
    "RecoverabilityValidation",
    "ReliabilityObservation",
    "ReliabilityVerification",
    "StabilityAssessment",
    "StabilitySample",
    "assess_stability",
    "summarize_diagnostics",
    "validate_recoverability",
    "verify_long_running",
    "verify_reliability",
    "production_reliability_compliance_check",
    # IP-3.6-E Mission Certification
    "ComplianceGroup",
    "ComplianceRegression",
    "MissionEngineeringReport",
    "MissionReadiness",
    "OperationalRegression",
    "ProductionCertification",
    "ReadinessGate",
    "RegressionSuite",
    "ReportSection",
    "TrackResult",
    "assess_mission_readiness",
    "build_engineering_report",
    "certify_end_to_end",
    "run_compliance_regression",
    "run_operational_regression",
    "mission_certification_compliance_check",
    # WP-29 integration
    "PlatformEngine",
    "PlatformPresentation",
    # WP-30..33 platform check gates
    "GateResult",
    "IntegrationCertification",
    "ReadinessAttributes",
    "certification_gate",
    "compliance_gate",
    "production_readiness_check",
    "regression_gate",
]
