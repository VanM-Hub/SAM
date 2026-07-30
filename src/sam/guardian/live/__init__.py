"""
SAM Guardian Live Runtime Foundation.

Synchronous event-driven runtime for Guardian internal communication.
All DTOs are frozen. No async, no threading, no network.

v5.2.0 — Added Transition Intelligence:
    transition.py, diff_engine.py, change_detector.py,
    impact.py, timeline.py, conversation_transition.py,
    dashboard_transition.py
"""

from .event import (
    GuardianEvent,
    GuardianEventType,
    GuardianEventPriority,
    GuardianEventSource,
    GuardianEventMetadata,
    GuardianEventSnapshot,
)
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

# Sprint 44 — Runtime Synchronization
from .state import (
    RuntimeState,
    RuntimeStatus,
    RuntimeHealth,
    RuntimeVersion,
    RuntimeStatistics,
    RuntimeSnapshot,
)
from .registry import GuardianRuntimeRegistry
from .synchronizer import GuardianRuntimeSynchronizer
from .snapshot import GuardianSnapshotManager
from .validator import GuardianConsistencyValidator
from .conversation_sync import LiveConversationSyncBridge
from .dashboard_sync import (
    LiveDashboardSyncBridge,
    RuntimeRegistryCard,
    SynchronizationCard,
    VersionMatrixCard,
    SnapshotCard,
    ConsistencyCard,
    SyncHealthCard,
)

# Sprint 45 — Transition Intelligence
from .transition import (
    RuntimeTransition,
    TransitionType,
    ImpactLevel,
    TransitionSummary,
    TransitionStatistics,
    TransitionHistory,
)
from .diff_engine import SnapshotDiffEngine
from .change_detector import ChangeDetector
from .impact import ImpactAnalyzer
from .timeline import TransitionTimeline
from .conversation_transition import LiveConversationTransitionBridge
from .dashboard_transition import (
    LiveDashboardTransitionBridge,
    RecentChangesCard,
    ImpactCard,
    TimelineCard,
    CriticalEventsCard,
    TransitionStatisticsCard,
    RuntimeEvolutionCard,
)

# Sprint 46 — Situation Intelligence
from .situation import (
    GuardianSituation, SituationType, SituationSeverity,
    SituationSummary, SituationStatistics, SituationSnapshot, SituationCandidate,
)
from .correlator import TransitionCorrelator
from .classifier import SituationClassifier
from .severity import SituationSeverityCalculator
from .history_situation import SituationHistory
from .conversation_situation import LiveConversationSituationBridge
from .dashboard_situation import (
    LiveDashboardSituationBridge as LiveDashboardSituationBridgeExport,
    CurrentSituationCard, SituationTimelineCard, SituationSeverityCard,
    SituationStatisticsCard, RuntimeDistributionCard, SituationHistoryCard,
)

__all__ = [
    # Sprint 43 — Core
    "GuardianEvent",
    "GuardianEventType",
    "GuardianEventPriority",
    "GuardianEventSource",
    "GuardianEventMetadata",
    "GuardianEventSnapshot",
    "GuardianEventPublisher",
    "GuardianEventSubscriber",
    "GuardianEventDispatcher",
    "EventHistory",
    "EventRecord",
    "HistoryStatistics",
    "GuardianLiveRuntime",
    "LiveConversationBridge",
    "LiveDashboardBridge",
    "LiveRuntimeCard",
    "RecentEventsCard",
    "DispatchStatusCard",
    "SubscribersCard",
    "RuntimeHealthCard",
    "GuardianActivityCard",
    "LiveReasoningBridge",
    "LiveLearningBridge",
    "LiveExecutionBridge",
    # Sprint 44 — Runtime Synchronization
    "RuntimeState",
    "RuntimeStatus",
    "RuntimeHealth",
    "RuntimeVersion",
    "RuntimeStatistics",
    "RuntimeSnapshot",
    "GuardianRuntimeRegistry",
    "GuardianRuntimeSynchronizer",
    "GuardianSnapshotManager",
    "GuardianConsistencyValidator",
    "LiveConversationSyncBridge",
    "LiveDashboardSyncBridge",
    "RuntimeRegistryCard",
    "SynchronizationCard",
    "VersionMatrixCard",
    "SnapshotCard",
    "ConsistencyCard",
    "SyncHealthCard",
    # Sprint 45 — Transition Intelligence
    "RuntimeTransition",
    "TransitionType",
    "ImpactLevel",
    "TransitionSummary",
    "TransitionStatistics",
    "TransitionHistory",
    "SnapshotDiffEngine",
    "ChangeDetector",
    "ImpactAnalyzer",
    "TransitionTimeline",
    "LiveConversationTransitionBridge",
    "LiveDashboardTransitionBridge",
    "RecentChangesCard",
    "ImpactCard",
    "TimelineCard",
    "CriticalEventsCard",
    "TransitionStatisticsCard",
    "RuntimeEvolutionCard",
    # Sprint 46 — Situation Intelligence
    "GuardianSituation",
    "SituationType",
    "SituationSeverity",
    "SituationSummary",
    "SituationStatistics",
    "SituationSnapshot",
    "SituationCandidate",
    "TransitionCorrelator",
    "SituationClassifier",
    "SituationSeverityCalculator",
    "SituationHistory",
    "LiveConversationSituationBridge",
    "LiveDashboardSituationBridgeExport",
    "CurrentSituationCard",
    "SituationTimelineCard",
    "SituationSeverityCard",
    "SituationStatisticsCard",
    "RuntimeDistributionCard",
    "SituationHistoryCard",
]
