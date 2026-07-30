"""
Approval Runtime V1 — Intake + Workflow Runtime.

Independent entry point for Approval Runtime.
Receives FinalDecisionRecord and runs intake + workflow pipeline.
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
        self._validator = IntakeValidator()
        self._normalizer = IntakeNormalizer()
        self._registry = IntakeRegistry()
        self._summary_builder = IntakeSummaryBuilder()
        self._workflow_engine = WorkflowEngine()
        self._workflow_builder = WorkflowBuilder(self._workflow_engine)

        self._last_validation: Optional[ValidationResult] = None
        self._last_summary: Optional[ApprovalIntakeSummary] = None
        self._last_normalized: Optional[NormalizedApprovalRecord] = None
        self._last_workflow: Optional[ApprovalWorkflow] = None

        self._c_intake = ConversationIntakeBridge(self)
        self._d_intake = DashboardIntakeBridge(self)
        self._c_workflow = ConversationWorkflowBridge(self)
        self._d_workflow = DashboardWorkflowBridge(self)

    @property
    def conversation(self): return self._c_intake
    @property
    def dashboard(self): return self._d_intake
    @property
    def conversation_workflow(self): return self._c_workflow
    @property
    def dashboard_workflow(self): return self._d_workflow

    def get_conversation(self, name: str):
        m = {"intake": self._c_intake, "workflow": self._c_workflow}
        return m.get(name, self._c_intake)

    def get_dashboard(self, name: str):
        m = {"intake": self._d_intake, "workflow": self._d_workflow}
        return m.get(name, self._d_intake)

    def process(self, record: ApprovalIntakeRecord) -> ApprovalRuntimeResult:
        # Validate
        validation = self._validator.validate(record)
        self._last_validation = validation

        if not validation.valid:
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

        return ApprovalRuntimeResult(
            success=True,
            record_id=record.record_id,
            validation=validation,
            normalized=normalized,
            summary=summary,
            workflow=workflow,
        )

    def get_status(self) -> Dict[str, Any]:
        return {
            "version": "6.1.0",
            "intake_count": self._registry.count if self._registry else 0,
            "workflow_count": self._workflow_engine.workflow_count,
            "last_record_id": self._registry.latest.record_id if self._registry and self._registry.latest else None,
        }
