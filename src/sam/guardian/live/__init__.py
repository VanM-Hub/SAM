"""
SAM Guardian Live Runtime Foundation.

Synchronous event-driven runtime for Guardian internal communication.
All DTOs are frozen. No async, no threading, no network.
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

__all__ = [
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
]
