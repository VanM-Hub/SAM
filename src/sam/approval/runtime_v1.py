"""
Approval Runtime V1 — Complete Runtime.

Full Approval Runtime with all engines integrated.
Does NOT auto-approve, auto-route, or auto-execute.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from .intake_record import ApprovalIntakeRecord, IntakeMetadata, IntakeSource
from .intake_validator import IntakeValidator, ValidationResult
from .intake_normalizer import IntakeNormalizer, NormalizedApprovalRecord
from .intake_registry import IntakeRegistry
from .intake_summary import IntakeSummaryBuilder, ApprovalIntakeSummary
from .conversation_intake import ConversationIntakeBridge
from .dashboard_intake import DashboardIntakeBridge
from .workflow import ApprovalWorkflow, WorkflowPhase
from .workflow_engine import WorkflowEngine, WorkflowTransitionError
from .workflow_builder import WorkflowBuilder
from .workflow_rules import WorkflowRules
from .conversation_workflow import ConversationWorkflowBridge
from .dashboard_workflow import DashboardWorkflowBridge
from .policy_engine import PolicyEngine
from .policy_validator import PolicyValidator
from .conversation_policy import ConversationPolicyBridge
from .dashboard_policy import DashboardPolicyBridge
from .multilevel_engine import MultiLevelEngine
from .multilevel_validator import MultiLevelValidator
from .conversation_multilevel import ConversationMultiLevelBridge
from .dashboard_multilevel import DashboardMultiLevelBridge
from .delegation_engine import DelegationEngine
from .conversation_delegation import ConversationDelegationBridge
from .dashboard_delegation import DashboardDelegationBridge
from .audit_engine import AuditEngine
from .conversation_audit import ConversationAuditBridge
from .dashboard_audit import DashboardAuditBridge
from .history_engine import HistoryEngine
from .conversation_history import ConversationHistoryBridge
from .dashboard_history import DashboardHistoryBridge
from .analytics_engine import AnalyticsEngine
from .conversation_analytics import ConversationAnalyticsBridge
from .dashboard_analytics import DashboardAnalyticsBridge
from .dashboard_engine import ApprovalDashboardEngine
from .console_engine import ConsoleEngine


@dataclass(frozen=True)
class ApprovalRuntimeResult:
    success: bool = False; record_id: str = ""
    validation: Optional[ValidationResult] = None
    normalized: Optional[NormalizedApprovalRecord] = None
    summary: Optional[ApprovalIntakeSummary] = None
    workflow: Optional[ApprovalWorkflow] = None
    error: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"success":self.success,"record_id":self.record_id,
        "validation":self.validation.to_dict() if self.validation else None,
        "normalized":self.normalized.to_dict() if self.normalized else None,
        "summary":self.summary.to_dict() if self.summary else None,
        "workflow":self.workflow.to_dict() if self.workflow else None,"error":self.error}


class ApprovalRuntimeV1:
    def __init__(self) -> None:
        self._version = "6.11.0"
        # Intake
        self._validator = IntakeValidator()
        self._normalizer = IntakeNormalizer()
        self._registry = IntakeRegistry()
        self._summary_builder = IntakeSummaryBuilder()
        # Workflow
        self._workflow_engine = WorkflowEngine()
        self._workflow_builder = WorkflowBuilder(self._workflow_engine)
        # Policy
        self._policy_engine = PolicyEngine()
        self._policy_validator = PolicyValidator()
        # Multi-Level
        self._multilevel_engine = MultiLevelEngine()
        # Delegation
        self._delegation_engine = DelegationEngine()
        # Audit
        self._audit_engine = AuditEngine()
        # History
        self._history_engine = HistoryEngine()
        # Analytics
        self._analytics_engine = AnalyticsEngine()
        # Dashboard
        self._dashboard_engine = ApprovalDashboardEngine()
        # Console
        self._console_engine = ConsoleEngine()

        self._last_validation: Optional[ValidationResult] = None
        self._last_summary: Optional[ApprovalIntakeSummary] = None
        self._last_normalized: Optional[NormalizedApprovalRecord] = None
        self._last_workflow: Optional[ApprovalWorkflow] = None

    # --- Bridges ---
    @property
    def conversation_intake(self): return ConversationIntakeBridge(self)
    @property
    def conversation_workflow(self): return ConversationWorkflowBridge(self)
    @property
    def conversation_policy(self): return ConversationPolicyBridge(self)
    @property
    def conversation_multilevel(self): return ConversationMultiLevelBridge(self)
    @property
    def conversation_delegation(self): return ConversationDelegationBridge(self)
    @property
    def conversation_audit(self): return ConversationAuditBridge(self)
    @property
    def conversation_history(self): return ConversationHistoryBridge(self)
    @property
    def conversation_analytics(self): return ConversationAnalyticsBridge(self)

    @property
    def dashboard_intake(self): return DashboardIntakeBridge(self)
    @property
    def dashboard_workflow(self): return DashboardWorkflowBridge(self)
    @property
    def dashboard_policy(self): return DashboardPolicyBridge(self)
    @property
    def dashboard_multilevel(self): return DashboardMultiLevelBridge(self)
    @property
    def dashboard_delegation(self): return DashboardDelegationBridge(self)
    @property
    def dashboard_audit(self): return DashboardAuditBridge(self)
    @property
    def dashboard_history(self): return DashboardHistoryBridge(self)
    @property
    def dashboard_analytics(self): return DashboardAnalyticsBridge(self)

    # --- Engines ---
    @property
    def policy_engine(self): return self._policy_engine
    @property
    def multilevel_engine(self): return self._multilevel_engine
    @property
    def delegation_engine(self): return self._delegation_engine
    @property
    def audit_engine(self): return self._audit_engine
    @property
    def history_engine(self): return self._history_engine
    @property
    def analytics_engine(self): return self._analytics_engine
    @property
    def dashboard_engine(self): return self._dashboard_engine
    @property
    def console_engine(self): return self._console_engine

    # --- Core Pipeline ---
    def process(self, record: ApprovalIntakeRecord) -> ApprovalRuntimeResult:
        # Validate
        validation = self._validator.validate(record)
        self._last_validation = validation

        if not validation.valid:
            self._audit_engine.log("VALIDATE_FAIL", "SYSTEM", record.record_id, "Validation failed")
            return ApprovalRuntimeResult(success=False, record_id=record.record_id,
                                          validation=validation, error="Validation failed")

        # Normalize
        normalized = self._normalizer.normalize(record)
        self._last_normalized = normalized

        # Register
        self._registry.register(record, normalized)

        # Summary
        summary = self._summary_builder.build(record, validation)
        self._last_summary = summary

        # Workflow
        workflow = self._workflow_builder.build(normalized)
        self._last_workflow = workflow

        # Audit
        self._audit_engine.log("PROCESS", "SYSTEM", record.record_id, f"Intake -> Workflow {workflow.workflow_id}")

        return ApprovalRuntimeResult(
            success=True,
            record_id=record.record_id,
            validation=validation,
            normalized=normalized,
            summary=summary,
            workflow=workflow,
        )

    def get_status(self) -> Dict[str, Any]:
        wf_all = list(self._workflow_engine.get_all().values())
        active_wf = sum(1 for w in wf_all if WorkflowRules.is_active(w.phase))
        terminal_wf = sum(1 for w in wf_all if WorkflowRules.is_terminal(w.phase))
        return {
            "version": self._version,
            "intake_count": self._registry.count if self._registry else 0,
            "workflow_count": self._workflow_engine.workflow_count,
            "active_workflows": active_wf,
            "completed_workflows": terminal_wf,
            "policy_count": self._policy_engine.policy_count,
            "multilevel_count": self._multilevel_engine.approval_count,
            "delegation_count": self._delegation_engine.rule_count,
            "audit_entries": self._audit_engine.entry_count,
            "history_entries": self._history_engine.entry_count,
            "analytics_metrics": len(self._analytics_engine.report().metrics),
            "dashboard_layouts": self._dashboard_engine.layout_count,
            "console_commands": len(self._console_engine.list_commands()),
        }
