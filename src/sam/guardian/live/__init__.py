"""
SAM Guardian Live Runtime Foundation.

Synchronous event-driven runtime for Guardian internal communication.
All DTOs are frozen. No async, no threading, no network.

v5.1.0 — Added Runtime Synchronization:
    state.py, registry.py, synchronizer.py, snapshot.py,
    validator.py, conversation_sync.py, dashboard_sync.py
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
]
