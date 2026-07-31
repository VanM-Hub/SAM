"""
Approval Runtime — Independent Approval Subsystem.
Phase VI: Sprint 64-75 | v6.11.0
"""

from .intake_record import ApprovalIntakeRecord, IntakeMetadata, IntakeSource
from .intake_validator import IntakeValidator, ValidationResult
from .intake_normalizer import IntakeNormalizer, NormalizedApprovalRecord
from .intake_registry import IntakeRegistry
from .intake_summary import IntakeSummaryBuilder, ApprovalIntakeSummary
from .conversation_intake import ConversationIntakeBridge
from .dashboard_intake import DashboardIntakeBridge
from .workflow import ApprovalWorkflow, WorkflowPhase, WorkflowTransition, PHASE_TRANSITIONS
from .workflow_engine import WorkflowEngine, WorkflowTransitionError
from .workflow_builder import WorkflowBuilder
from .workflow_rules import WorkflowRules
from .conversation_workflow import ConversationWorkflowBridge
from .dashboard_workflow import DashboardWorkflowBridge
from .policy import ApprovalPolicy, PolicyEffect, PolicyCondition, PolicyEvaluationResult
from .policy_engine import PolicyEngine
from .policy_builder import PolicyBuilder
from .policy_validator import PolicyValidator
from .conversation_policy import ConversationPolicyBridge
from .dashboard_policy import DashboardPolicyBridge
from .multilevel import ApprovalLevel, MultiLevelApproval
from .multilevel_engine import MultiLevelEngine
from .multilevel_builder import MultiLevelBuilder
from .multilevel_validator import MultiLevelValidator
from .conversation_multilevel import ConversationMultiLevelBridge
from .dashboard_multilevel import DashboardMultiLevelBridge
from .delegation import DelegationRule
from .delegation_engine import DelegationEngine
from .conversation_delegation import ConversationDelegationBridge
from .dashboard_delegation import DashboardDelegationBridge
from .audit import AuditEntry, AuditLog
from .audit_engine import AuditEngine
from .conversation_audit import ConversationAuditBridge
from .dashboard_audit import DashboardAuditBridge
from .history import HistoryEntry, ApprovalHistory
from .history_engine import HistoryEngine
from .conversation_history import ConversationHistoryBridge
from .dashboard_history import DashboardHistoryBridge
from .analytics import AnalyticsMetric, AnalyticsReport
from .analytics_engine import AnalyticsEngine
from .conversation_analytics import ConversationAnalyticsBridge
from .dashboard_analytics import DashboardAnalyticsBridge
from .dashboard import DashboardWidget, DashboardLayout
from .dashboard_engine import ApprovalDashboardEngine
from .console import ConsoleCommand, ConsoleResponse
from .console_engine import ConsoleEngine
from .runtime_v1 import ApprovalRuntimeV1, ApprovalRuntimeResult

__all__ = [
    # Intake
    "ApprovalIntakeRecord", "IntakeMetadata", "IntakeSource",
    "IntakeValidator", "ValidationResult",
    "IntakeNormalizer", "NormalizedApprovalRecord",
    "IntakeRegistry",
    "IntakeSummaryBuilder", "ApprovalIntakeSummary",
    "ConversationIntakeBridge", "DashboardIntakeBridge",
    # Workflow
    "ApprovalWorkflow", "WorkflowPhase", "WorkflowTransition", "PHASE_TRANSITIONS",
    "WorkflowEngine", "WorkflowTransitionError",
    "WorkflowBuilder",
    "WorkflowRules",
    "ConversationWorkflowBridge", "DashboardWorkflowBridge",
    # Policy
    "ApprovalPolicy", "PolicyEffect", "PolicyCondition", "PolicyEvaluationResult",
    "PolicyEngine",
    "PolicyBuilder",
    "PolicyValidator",
    "ConversationPolicyBridge", "DashboardPolicyBridge",
    # Multilevel
    "ApprovalLevel", "MultiLevelApproval",
    "MultiLevelEngine",
    "MultiLevelBuilder",
    "MultiLevelValidator",
    "ConversationMultiLevelBridge", "DashboardMultiLevelBridge",
    # Delegation
    "DelegationRule",
    "DelegationEngine",
    "ConversationDelegationBridge", "DashboardDelegationBridge",
    # Audit
    "AuditEntry", "AuditLog",
    "AuditEngine",
    "ConversationAuditBridge", "DashboardAuditBridge",
    # History
    "HistoryEntry", "ApprovalHistory",
    "HistoryEngine",
    "ConversationHistoryBridge", "DashboardHistoryBridge",
    # Analytics
    "AnalyticsMetric", "AnalyticsReport",
    "AnalyticsEngine",
    "ConversationAnalyticsBridge", "DashboardAnalyticsBridge",
    # Dashboard & Console
    "DashboardWidget", "DashboardLayout",
    "ApprovalDashboardEngine",
    "ConsoleCommand", "ConsoleResponse",
    "ConsoleEngine",
    # Runtime
    "ApprovalRuntimeV1", "ApprovalRuntimeResult",
]
