"""
Guardian Live Runtime.

Central runtime that orchestrates the live event pipeline:
    Receive Event → Dispatch → Guardian → Reasoning → Learning
    → Execution Preview → Dashboard → Conversation

Synchronous only. No async, no threading, no network.
All calls go through existing bridges. Does not modify legacy runtime.
"""

from typing import Optional, Dict, List, Any
from datetime import datetime

from .event import (
    GuardianEvent,
    GuardianEventType,
    GuardianEventPriority,
    GuardianEventSource,
    GuardianEventMetadata,
    GuardianEventSnapshot,
)
from .dispatcher import GuardianEventDispatcher
from .publisher import GuardianEventPublisher
from .subscriber import GuardianEventSubscriber
from .history import EventHistory, EventRecord
from .conversation import LiveConversationBridge
from .dashboard import LiveDashboardBridge
from .reasoning_bridge import LiveReasoningBridge
from .learning_bridge import LiveLearningBridge
from .execution_bridge import LiveExecutionBridge


class GuardianLiveRuntime:
    """
    Synchronous live runtime for the Guardian.

    Full Pipeline:
        Receive Event
        ↓
        Dispatch
        ↓
        Guardian
        ↓
        Reasoning
        ↓
        Learning
        ↓
        Execution Preview
        ↓
        Dashboard
        ↓
        Conversation

    Does NOT replace the existing Guardian Runtime.
    All calls synchronous, DTO-only, preview only.
    """

    def __init__(
        self,
        history_max_size: int = 1000,
    ) -> None:
        self._dispatcher = GuardianEventDispatcher()
        self._publisher = GuardianEventPublisher(self._dispatcher)
        self._history = EventHistory(max_size=history_max_size)
        self._conversation = LiveConversationBridge(self)
        self._dashboard = LiveDashboardBridge(self)
        self._reasoning = LiveReasoningBridge(self)
        self._learning = LiveLearningBridge(self)
        self._execution = LiveExecutionBridge(self)
        self._is_running: bool = False

    # --- Lifecycle ---

    def start(self) -> None:
        """Start the live runtime."""
        self._is_running = True

    def stop(self) -> None:
        """Stop the live runtime."""
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """Check if runtime is running."""
        return self._is_running

    # --- Publishing ---

    @property
    def publisher(self) -> GuardianEventPublisher:
        """Get the event publisher."""
        return self._publisher

    def publish(
        self,
        event_type: GuardianEventType,
        source: GuardianEventSource,
        payload: object,
        priority: Optional[GuardianEventPriority] = None,
        correlation_id: Optional[str] = None,
    ) -> GuardianEvent:
        """
        Publish an event through the live runtime.

        Args:
            event_type: Type of event.
            source: Source component.
            payload: Event payload.
            priority: Priority level.
            correlation_id: Optional correlation ID.

        Returns:
            The published GuardianEvent.
        """
        return self._publisher.publish(
            event_type=event_type,
            source=source,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id,
        )

    # --- Subscribers ---

    def register_subscriber(self, subscriber: GuardianEventSubscriber) -> None:
        """Register an event subscriber."""
        self._dispatcher.register(subscriber)

    def unregister_subscriber(self, subscriber: GuardianEventSubscriber) -> None:
        """Unregister an event subscriber."""
        self._dispatcher.unregister(subscriber)

    @property
    def dispatcher(self) -> GuardianEventDispatcher:
        """Get the event dispatcher."""
        return self._dispatcher

    # --- Bridges ---

    @property
    def conversation(self) -> LiveConversationBridge:
        """Get the live conversation bridge."""
        return self._conversation

    @property
    def dashboard(self) -> LiveDashboardBridge:
        """Get the live dashboard bridge."""
        return self._dashboard

    @property
    def reasoning(self) -> LiveReasoningBridge:
        """Get the live reasoning bridge."""
        return self._reasoning

    @property
    def learning(self) -> LiveLearningBridge:
        """Get the live learning bridge."""
        return self._learning

    @property
    def execution(self) -> LiveExecutionBridge:
        """Get the live execution bridge."""
        return self._execution

    # --- History ---

    def record_dispatch(
        self,
        event: GuardianEvent,
        processing_ms: float,
        subscriber_count: int,
        error_count: int,
    ) -> None:
        """Record an event dispatch in history."""
        self._history.record(
            event=event,
            processing_ms=processing_ms,
            subscriber_count=subscriber_count,
            error_count=error_count,
        )

    @property
    def history(self) -> EventHistory:
        """Get the event history."""
        return self._history

    @property
    def last_snapshot(self) -> Optional[GuardianEventSnapshot]:
        """Get the last dispatch snapshot."""
        return self._dispatcher.last_snapshot

    # --- Status ---

    def get_status(self) -> Dict[str, Any]:
        """Get live runtime status as a dict."""
        return {
            "is_running": self._is_running,
            "subscriber_count": self._dispatcher.subscriber_count,
            "total_dispatched": self._dispatcher.total_dispatched,
            "error_count": self._dispatcher.error_count,
            "history_count": self._history.count,
            "subscribers": self._dispatcher.get_subscriber_names(),
            "dashboard_cards": self._dashboard.card_count,
            "conversation_queries": self._conversation.query_count,
            "reasoning_triggers": self._reasoning.trigger_count,
            "learning_feeds": self._learning.feed_count,
            "execution_previews": self._execution.preview_count,
        }

    # --- Pipeline Execution ---

    def execute_pipeline(
        self,
        observation_payload: Optional[object] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full live pipeline.

        Pipeline:
            1. Create observation event
            2. Dispatch to guardian
            3. Forward to reasoning
            4. Forward to learning
            5. Forward to execution preview
            6. Update dashboard cards
            7. Return pipeline result

        Args:
            observation_payload: Optional observation data.

        Returns:
            Dict with pipeline results.
        """
        if not self._is_running:
            return {"status": "stopped", "error": "Runtime is not running"}

        # Step 1: Create observation event
        event = self.publish(
            event_type=GuardianEventType.OBSERVATION_UPDATE,
            source=GuardianEventSource.OBSERVATION,
            payload=observation_payload or {},
            priority=GuardianEventPriority.MEDIUM,
        )

        # Step 2: Dispatch and get snapshot
        snapshot = self._dispatcher.last_snapshot

        # Step 3: Record in history
        if snapshot:
            self.record_dispatch(
                event=event,
                processing_ms=snapshot.duration_ms,
                subscriber_count=len(self._dispatcher.subscribers),
                error_count=len(snapshot.errors),
            )

            # Step 4: Pipeline cascade (synchronous, DTO-only)
            if not snapshot.errors:
                # 4a. Reasoning
                reasoning_result = self._reasoning.trigger(event)
                # 4b. Learning
                learning_result = self._learning.feed(event)
                # 4c. Execution Preview
                execution_result = self._execution.preview(event)
                # 4d. Dashboard refresh
                self._dashboard.refresh()
                # 4e. Conversation update
                self._conversation.update()

        return {
            "event_id": event.event_id,
            "snapshot": snapshot.to_dict() if snapshot else None,
            "pipeline": {
                "reasoning": reasoning_result if snapshot else None,
                "learning": learning_result if snapshot else None,
                "execution_preview": execution_result if snapshot else None,
            } if snapshot and not snapshot.errors else None,
            "is_running": self._is_running,
        }
