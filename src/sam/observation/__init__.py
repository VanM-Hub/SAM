"""Observation Layer — Read-Only Presentation & Observation.

MISSION-2C (C-Phase 1): Operational Intelligence.
Prinsip: Observe, never govern.

Modul ini tidak punya runtime, tidak punya governance, tidak punya orchestration.
Pure read-only: membaca data yang sudah dipublikasikan oleh runtime resmi.

Constraints (AP-2C-001):
- Tidak menambah runtime
- Tidak mengubah governance flow
- Tidak mengubah runtime responsibility
- Tidak mengubah Foundation
- Tidak ada business logic
- Tidak ada execution/approval/workflow/policy mutation
"""
from __future__ import annotations

# C-Phase 3: Observation Recommendation Engine exports
from sam.observation.recommendation import (
    ObservationRecommendation,
    ObservationRecommendationEngine,
    OperationalRecommendationReport,
)

# C-Phase 3 (Workstream C1-C5): Operational Intelligence observers
from sam.observation.mission_intelligence import (
    MissionCheckpointView,
    MissionHealthView,
    MissionIntelligenceObserver,
    MissionIntelligenceReport,
    MissionProgressView,
    MissionStatusView,
    MissionTimelineView,
)
from sam.observation.workflow_intelligence import (
    Bottleneck,
    WorkflowBottleneckView,
    WorkflowDependencyGraph,
    WorkflowIntelligenceObserver,
    WorkflowIntelligenceReport,
    WorkflowStepDependency,
    WorkflowView,
)
from sam.observation.approval_intelligence import (
    ApprovalIntelligenceObserver,
    ApprovalIntelligenceReport,
    ApprovalMetric,
    ApprovalMetrics,
    ApprovalQueue,
    ApprovalQueueEntry,
    DecisionHistory,
    DecisionHistoryEntry,
)
from sam.observation.execution_intelligence import (
    ExecutionAnalytics,
    ExecutionIntelligenceObserver,
    ExecutionIntelligenceReport,
    ExecutionTimeline,
    ExecutionTimelineEntry,
    ExecutionView,
)
from sam.observation.audit_intelligence import (
    AuditCorrelation,
    AuditIntelligenceObserver,
    AuditIntelligenceReport,
    AuditView,
    ComplianceStatus,
)

# C-Phase 4: Workstream C6 Capability Operational Intelligence
from sam.observation.capability_intelligence import (
    CapabilityAggregation,
    CapabilityDependency,
    CapabilityDependencyView,
    CapabilityHealthEntry,
    CapabilityHealthReport,
    CapabilityIntelligenceObserver,
    CapabilityReadinessEntry,
    CapabilityReadinessReport,
    CapabilityStatusEntry,
)

# C-Phase 2: Gap Resolution exports
from sam.observation.gaps import (
    ApprovalHealthDetail,
    ApprovalHealthInspector,
    EventBusDescriptor,
    EventBusInspector,
    EventBusRegistry,
    GapResolutionCoordinator,
    GapResolutionReport,
    OperationalAnalytics,
    OperationalAnalyticsReport,
    OperationalTrend,
    PerRuntimeHealthDetail,
    PreviewAvailability,
    PreviewAvailabilityIndex,
    PreviewConsumerIndex,
    ReadinessDetail,
    ReadinessReport,
    ReadinessReporter,
    UnifiedHealthReport,
    UnifiedHealthReporter,
)

__all__ = [
    # GAP-001
    "PerRuntimeHealthDetail",
    "UnifiedHealthReport",
    "UnifiedHealthReporter",
    # GAP-002
    "PreviewAvailability",
    "PreviewAvailabilityIndex",
    "PreviewConsumerIndex",
    # GAP-003
    "EventBusDescriptor",
    "EventBusRegistry",
    "EventBusInspector",
    # GAP-004
    "ReadinessDetail",
    "ReadinessReport",
    "ReadinessReporter",
    # GAP-005
    "OperationalTrend",
    "OperationalAnalyticsReport",
    "OperationalAnalytics",
    # GAP-006
    "ApprovalHealthDetail",
    "ApprovalHealthInspector",
    # Coordinator
    "GapResolutionCoordinator",
    "GapResolutionReport",
    # C-Phase 3: Observation Recommendation Engine
    "ObservationRecommendation",
    "ObservationRecommendationEngine",
    "OperationalRecommendationReport",
    # C-Phase 3: Workstream C1 Mission
    "MissionCheckpointView",
    "MissionTimelineView",
    "MissionStatusView",
    "MissionProgressView",
    "MissionHealthView",
    "MissionIntelligenceReport",
    "MissionIntelligenceObserver",
    # C-Phase 3: Workstream C2 Workflow
    "WorkflowView",
    "WorkflowStepDependency",
    "WorkflowDependencyGraph",
    "Bottleneck",
    "WorkflowBottleneckView",
    "WorkflowIntelligenceReport",
    "WorkflowIntelligenceObserver",
    # C-Phase 3: Workstream C3 Approval
    "ApprovalQueueEntry",
    "ApprovalQueue",
    "DecisionHistoryEntry",
    "DecisionHistory",
    "ApprovalMetric",
    "ApprovalMetrics",
    "ApprovalIntelligenceReport",
    "ApprovalIntelligenceObserver",
    # C-Phase 3: Workstream C4 Execution
    "ExecutionView",
    "ExecutionTimelineEntry",
    "ExecutionTimeline",
    "ExecutionAnalytics",
    "ExecutionIntelligenceReport",
    "ExecutionIntelligenceObserver",
    # C-Phase 3: Workstream C5 Audit
    "AuditView",
    "AuditCorrelation",
    "ComplianceStatus",
    "AuditIntelligenceReport",
    "AuditIntelligenceObserver",
    # C-Phase 4: Workstream C6 Capability
    "CapabilityStatusEntry",
    "CapabilityAggregation",
    "CapabilityReadinessEntry",
    "CapabilityReadinessReport",
    "CapabilityHealthEntry",
    "CapabilityHealthReport",
    "CapabilityDependency",
    "CapabilityDependencyView",
    "CapabilityIntelligenceObserver",
]
