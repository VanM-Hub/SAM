"""Universal Workflow Integration - MISSION-5.4.

Mengintegrasikan Workflow sebagai Citizen: definisi deklaratif, komposisi &
dependency, eksekusi yang governed, state/recovery/learning, sertifikasi.

IP-5.4-001: Universal Workflow Foundation.
IP-5.4-002: Workflow Composition & Dependency.
IP-5.4-003: Governed Workflow Execution.
IP-5.4-004: Workflow State, Recovery & Learning.
IP-5.4-005: Universal Workflow Certification.
"""
from __future__ import annotations

# IP-5.4-001 - Foundation
from .workflow_foundation import (
    StepDependency,
    StepKind,
    StepState,
    WorkflowComplianceChecker,
    WorkflowComplianceResult,
    WorkflowDefinition,
    WorkflowExplainer,
    WorkflowIdentity,
    WorkflowInput,
    WorkflowOutput,
    WorkflowPersistence,
    WorkflowState,
    WorkflowStateMachine,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTraceEntry,
    WorkflowValidationResult,
    WorkflowValidator,
)

# IP-5.4-002 - Composition & Dependency
from .workflow_composition import (
    CapabilityBinding,
    CompositionExplainer,
    CompositionResult,
    ConditionalTransition,
    DependencyResolver,
    MappingRule,
    WorkflowComposer,
)

# IP-5.4-003 - Governed Execution
from .workflow_execution import (
    DecisionRecord,
    ExecutionComplianceChecker,
    ExecutionComplianceResult,
    ExecutionContext,
    ExecutionRequest,
    ExecutionStage,
    ExecutionTrace,
    FailurePropagator,
    StepExecutionResult,
    StepResultHandler,
    WorkflowExecutionEngine,
)

# IP-5.4-004 - State, Recovery & Learning
from .workflow_state_recovery import (
    FailureRecoveryModel,
    IdempotencyGuard,
    IdempotencyManager,
    LearningEvidence,
    LearningEvidenceCollector,
    OutcomeAnalyzer,
    Phase,
    RecoveryComplianceChecker,
    RecoveryComplianceResult,
    RecoveryExplainability,
    RetryPolicy,
    StateTransition,
    WorkflowOutcome,
    WorkflowReplayer,
    WorkflowStateMachine as RecoveryStateMachine,
)

# IP-5.4-005 - Certification
from .workflow_certification import (
    WorkflowCertEvidence,
    WorkflowCertStatus,
    WorkflowCertification,
)

__all__ = [
    "StepDependency", "StepKind", "StepState", "WorkflowComplianceChecker",
    "WorkflowComplianceResult", "WorkflowDefinition", "WorkflowExplainer",
    "WorkflowIdentity", "WorkflowInput", "WorkflowOutput", "WorkflowPersistence",
    "WorkflowState", "WorkflowStateMachine", "WorkflowStatus", "WorkflowStep",
    "WorkflowTraceEntry", "WorkflowValidationResult", "WorkflowValidator",
    "CapabilityBinding", "CompositionExplainer", "CompositionResult",
    "ConditionalTransition", "DependencyResolver", "MappingRule", "WorkflowComposer",
    "DecisionRecord", "ExecutionComplianceChecker", "ExecutionComplianceResult",
    "ExecutionContext", "ExecutionRequest", "ExecutionStage", "ExecutionTrace",
    "FailurePropagator", "StepExecutionResult", "StepResultHandler",
    "WorkflowExecutionEngine",
    "FailureRecoveryModel", "IdempotencyGuard", "IdempotencyManager",
    "LearningEvidence", "LearningEvidenceCollector", "OutcomeAnalyzer", "Phase",
    "RecoveryComplianceChecker", "RecoveryComplianceResult", "RecoveryExplainability",
    "RetryPolicy", "StateTransition", "WorkflowOutcome", "WorkflowReplayer",
    "RecoveryStateMachine",
    "WorkflowCertEvidence", "WorkflowCertStatus", "WorkflowCertification",
]
