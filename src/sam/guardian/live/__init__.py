"""
SAM Guardian Live Runtime Foundation.

Synchronous event-driven runtime for Guardian internal communication.
All DTOs are frozen. No async, no threading, no network.

v5.4.0 — Added Operational Assessment:
    assessment.py, assessment_builder.py, risk_assessment.py,
    priority_assessment.py, confidence.py, conversation_assessment.py,
    dashboard_assessment.py
"""

# Sprint 43 - Core
from .event import GuardianEvent, GuardianEventType, GuardianEventPriority, GuardianEventSource, GuardianEventMetadata, GuardianEventSnapshot
from .publisher import GuardianEventPublisher
from .subscriber import GuardianEventSubscriber
from .dispatcher import GuardianEventDispatcher
from .history import EventHistory, EventRecord, HistoryStatistics
from .runtime import GuardianLiveRuntime
from .conversation import LiveConversationBridge
from .dashboard import LiveDashboardBridge, LiveRuntimeCard, RecentEventsCard, DispatchStatusCard, SubscribersCard, RuntimeHealthCard, GuardianActivityCard
from .reasoning_bridge import LiveReasoningBridge
from .learning_bridge import LiveLearningBridge
from .execution_bridge import LiveExecutionBridge

# Sprint 44 - Runtime Synchronization
from .state import RuntimeState, RuntimeStatus, RuntimeHealth, RuntimeVersion, RuntimeStatistics, RuntimeSnapshot
from .registry import GuardianRuntimeRegistry
from .synchronizer import GuardianRuntimeSynchronizer
from .snapshot import GuardianSnapshotManager
from .validator import GuardianConsistencyValidator
from .conversation_sync import LiveConversationSyncBridge
from .dashboard_sync import LiveDashboardSyncBridge, RuntimeRegistryCard, SynchronizationCard, VersionMatrixCard, SnapshotCard, ConsistencyCard, SyncHealthCard

# Sprint 45 - Transition Intelligence
from .transition import RuntimeTransition, TransitionType, ImpactLevel, TransitionSummary, TransitionStatistics, TransitionHistory
from .diff_engine import SnapshotDiffEngine
from .change_detector import ChangeDetector
from .impact import ImpactAnalyzer
from .timeline import TransitionTimeline
from .conversation_transition import LiveConversationTransitionBridge
from .dashboard_transition import LiveDashboardTransitionBridge, RecentChangesCard, ImpactCard, TimelineCard, CriticalEventsCard, TransitionStatisticsCard, RuntimeEvolutionCard

# Sprint 46 - Situation Intelligence
from .situation import GuardianSituation, SituationType, SituationSeverity, SituationSummary, SituationStatistics, SituationSnapshot, SituationCandidate
from .correlator import TransitionCorrelator
from .classifier import SituationClassifier
from .severity import SituationSeverityCalculator
from .history_situation import SituationHistory
from .conversation_situation import LiveConversationSituationBridge
from .dashboard_situation import LiveDashboardSituationBridge as LiveDashboardSituationBridgeExport, CurrentSituationCard, SituationTimelineCard, SituationSeverityCard, SituationStatisticsCard, RuntimeDistributionCard, SituationHistoryCard

# Sprint 47 - Operational Assessment
from .assessment import GuardianAssessment, AssessmentLevel, AssessmentCategory, RiskLevel, PriorityLevel, AssessmentSummary, AssessmentStatistics, AssessmentSnapshot
from .assessment_builder import AssessmentBuilder
from .risk_assessment import RiskAssessor
from .priority_assessment import PriorityAssessor
from .confidence import ConfidenceEngine
from .conversation_assessment import LiveConversationAssessmentBridge
from .dashboard_assessment import LiveDashboardAssessmentBridge as LiveDashboardAssessmentBridgeExport, AssessmentOverviewCard, RiskMatrixCard, PriorityMatrixCard, ConfidenceCard, RuntimeRiskCard, AssessmentHistoryCard

__all__ = [
    "GuardianEvent","GuardianEventType","GuardianEventPriority","GuardianEventSource","GuardianEventMetadata","GuardianEventSnapshot",
    "GuardianEventPublisher","GuardianEventSubscriber","GuardianEventDispatcher","EventHistory","EventRecord","HistoryStatistics",
    "GuardianLiveRuntime","LiveConversationBridge","LiveDashboardBridge","LiveRuntimeCard","RecentEventsCard","DispatchStatusCard","SubscribersCard","RuntimeHealthCard","GuardianActivityCard",
    "LiveReasoningBridge","LiveLearningBridge","LiveExecutionBridge",
    "RuntimeState","RuntimeStatus","RuntimeHealth","RuntimeVersion","RuntimeStatistics","RuntimeSnapshot",
    "GuardianRuntimeRegistry","GuardianRuntimeSynchronizer","GuardianSnapshotManager","GuardianConsistencyValidator",
    "LiveConversationSyncBridge","LiveDashboardSyncBridge",
    "RuntimeRegistryCard","SynchronizationCard","VersionMatrixCard","SnapshotCard","ConsistencyCard","SyncHealthCard",
    "RuntimeTransition","TransitionType","ImpactLevel","TransitionSummary","TransitionStatistics","TransitionHistory",
    "SnapshotDiffEngine","ChangeDetector","ImpactAnalyzer","TransitionTimeline",
    "LiveConversationTransitionBridge","LiveDashboardTransitionBridge",
    "RecentChangesCard","ImpactCard","TimelineCard","CriticalEventsCard","TransitionStatisticsCard","RuntimeEvolutionCard",
    "GuardianSituation","SituationType","SituationSeverity","SituationSummary","SituationStatistics","SituationSnapshot","SituationCandidate",
    "TransitionCorrelator","SituationClassifier","SituationSeverityCalculator","SituationHistory",
    "LiveConversationSituationBridge","LiveDashboardSituationBridgeExport",
    "CurrentSituationCard","SituationTimelineCard","SituationSeverityCard","SituationStatisticsCard","RuntimeDistributionCard","SituationHistoryCard",
    "GuardianAssessment","AssessmentLevel","AssessmentCategory","RiskLevel","PriorityLevel","AssessmentSummary","AssessmentStatistics","AssessmentSnapshot",
    "AssessmentBuilder","RiskAssessor","PriorityAssessor","ConfidenceEngine",
    "LiveConversationAssessmentBridge","LiveDashboardAssessmentBridgeExport",
    "AssessmentOverviewCard","RiskMatrixCard","PriorityMatrixCard","ConfidenceCard","RuntimeRiskCard","AssessmentHistoryCard",
]
