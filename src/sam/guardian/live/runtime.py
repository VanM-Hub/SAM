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
from .registry import GuardianRuntimeRegistry
from .synchronizer import GuardianRuntimeSynchronizer
from .snapshot import GuardianSnapshotManager
from .validator import GuardianConsistencyValidator
from .conversation_sync import LiveConversationSyncBridge
from .dashboard_sync import LiveDashboardSyncBridge
from .diff_engine import SnapshotDiffEngine
from .change_detector import ChangeDetector
from .impact import ImpactAnalyzer
from .timeline import TransitionTimeline
from .conversation_transition import LiveConversationTransitionBridge
from .dashboard_transition import LiveDashboardTransitionBridge
from .classifier import SituationClassifier
from .history_situation import SituationHistory
from .conversation_situation import LiveConversationSituationBridge
from .dashboard_situation import LiveDashboardSituationBridge as LiveDashboardSituationBridgeCls
from .assessment_builder import AssessmentBuilder
from .conversation_assessment import LiveConversationAssessmentBridge
from .dashboard_assessment import LiveDashboardAssessmentBridge as LiveDashboardAssessmentBridgeCls
from .intent_builder import IntentBuilder
from .intent_policy import IntentPolicyEngine
from .intent_ranker import IntentRanker
from .intent_validator import IntentValidator
from .conversation_intent import LiveConversationIntentBridge
from .dashboard_intent import LiveDashboardIntentBridge as LiveDashboardIntentBridgeCls


class GuardianLiveRuntime:
    """
    Synchronous live runtime for the Guardian.

    Full Pipeline (v5.5.0):
        Event → Dispatch → Synchronization
        → Transition Intelligence → Situation Intelligence
        → Operational Assessment → Operational Intent
        → Guardian → Reasoning → Learning
        → Execution Preview → Dashboard → Conversation

    Does NOT replace the existing Guardian Runtime.
    Intent is DTO only — does NOT execute, create missions, or call Decision Runtime.
    """

    def __init__(
        self,
        history_max_size: int = 1000,
        runtime_id: Optional[str] = None,
    ) -> None:
        self._dispatcher = GuardianEventDispatcher()
        self._publisher = GuardianEventPublisher(self._dispatcher)
        self._history = EventHistory(max_size=history_max_size)
        self._conversation = LiveConversationBridge(self)
        self._dashboard = LiveDashboardBridge(self)
        self._reasoning = LiveReasoningBridge(self)
        self._learning = LiveLearningBridge(self)
        self._execution = LiveExecutionBridge(self)

        # Sprint 44 — Synchronization
        self._registry = GuardianRuntimeRegistry()
        self._synchronizer = GuardianRuntimeSynchronizer(self._registry)
        self._snapshot_manager = GuardianSnapshotManager()
        self._validator = GuardianConsistencyValidator(self._registry, self._snapshot_manager)
        self._conversation_sync = LiveConversationSyncBridge(self)
        self._dashboard_sync = LiveDashboardSyncBridge(self)

        # Sprint 45 — Transition Intelligence
        self._diff_engine = SnapshotDiffEngine()
        self._change_detector = ChangeDetector()
        self._impact_analyzer = ImpactAnalyzer()
        self._timeline = TransitionTimeline()
        self._conversation_transition = LiveConversationTransitionBridge(self)
        self._dashboard_transition = LiveDashboardTransitionBridge(self)
        self._last_registry_count: int = 0

        # Sprint 46 — Situation Intelligence
        self._classifier = SituationClassifier()
        self._situation_history = SituationHistory()
        self._conversation_situation = LiveConversationSituationBridge(self)
        self._dashboard_situation = LiveDashboardSituationBridgeCls(self)

        # Sprint 47 — Operational Assessment
        self._assessment_builder = AssessmentBuilder()
        self._assessment_history: 'List[GuardianAssessment]' = []
        self._conversation_assessment = LiveConversationAssessmentBridge(self)
        self._dashboard_assessment = LiveDashboardAssessmentBridgeCls(self)

        # Sprint 48 — Operational Intent
        self._intent_builder = IntentBuilder()
        self._intent_policy = IntentPolicyEngine()
        self._intent_ranker = IntentRanker()
        self._intent_validator = IntentValidator()
        self._intent_history: 'List[GuardianIntent]' = []
        self._conversation_intent = LiveConversationIntentBridge(self)
        self._dashboard_intent = LiveDashboardIntentBridgeCls(self)

        self._is_running: bool = False
        if runtime_id:
            self._synchronizer.set_runtime_id(runtime_id)

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

    # --- Sprint 44 — Synchronization ---

    @property
    def registry(self) -> GuardianRuntimeRegistry:
        """Get the runtime registry."""
        return self._registry

    @property
    def synchronizer(self) -> GuardianRuntimeSynchronizer:
        """Get the runtime synchronizer."""
        return self._synchronizer

    @property
    def snapshot_manager(self) -> GuardianSnapshotManager:
        """Get the snapshot manager."""
        return self._snapshot_manager

    @property
    def validator(self) -> GuardianConsistencyValidator:
        """Get the consistency validator."""
        return self._validator

    @property
    def conversation_sync(self) -> 'LiveConversationSyncBridge':
        """Get the conversation sync bridge."""
        return self._conversation_sync

    @property
    def dashboard_sync(self) -> 'LiveDashboardSyncBridge':
        """Get the dashboard sync bridge."""
        return self._dashboard_sync

    # --- Sprint 45 — Transition Intelligence ---

    @property
    def diff_engine(self) -> SnapshotDiffEngine:
        """Get the snapshot diff engine."""
        return self._diff_engine

    @property
    def change_detector(self) -> ChangeDetector:
        """Get the change detector."""
        return self._change_detector

    @property
    def impact_analyzer(self) -> ImpactAnalyzer:
        """Get the impact analyzer."""
        return self._impact_analyzer

    @property
    def timeline(self) -> TransitionTimeline:
        """Get the transition timeline."""
        return self._timeline

    @property
    def conversation_transition(self) -> 'LiveConversationTransitionBridge':
        """Get the conversation transition bridge."""
        return self._conversation_transition

    @property
    def dashboard_transition(self) -> 'LiveDashboardTransitionBridge':
        """Get the dashboard transition bridge."""
        return self._dashboard_transition

    # --- Sprint 46 — Situation Intelligence ---

    @property
    def classifier(self) -> 'SituationClassifier':
        """Get the situation classifier."""
        return self._classifier

    @property
    def situation_history(self) -> 'SituationHistory':
        """Get the situation history."""
        return self._situation_history

    @property
    def conversation_situation(self) -> 'LiveConversationSituationBridge':
        """Get the conversation situation bridge."""
        return self._conversation_situation

    @property
    def dashboard_situation(self) -> 'LiveDashboardSituationBridgeCls':
        """Get the dashboard situation bridge."""
        return self._dashboard_situation

    # --- Sprint 47 — Operational Assessment ---

    @property
    def assessment_builder(self) -> 'AssessmentBuilder':
        """Get the assessment builder."""
        return self._assessment_builder

    @property
    def assessment_history(self) -> 'List[GuardianAssessment]':
        """Get the assessment history."""
        return list(self._assessment_history)

    @property
    def conversation_assessment(self) -> 'LiveConversationAssessmentBridge':
        """Get the conversation assessment bridge."""
        return self._conversation_assessment

    @property
    def dashboard_assessment(self) -> 'LiveDashboardAssessmentBridgeCls':
        """Get the dashboard assessment bridge."""
        return self._dashboard_assessment

    # --- Sprint 48 — Operational Intent ---

    @property
    def intent_builder(self) -> 'IntentBuilder':
        """Get the intent builder."""
        return self._intent_builder

    @property
    def intent_policy(self) -> 'IntentPolicyEngine':
        """Get the intent policy engine."""
        return self._intent_policy

    @property
    def intent_ranker(self) -> 'IntentRanker':
        """Get the intent ranker."""
        return self._intent_ranker

    @property
    def intent_validator(self) -> 'IntentValidator':
        """Get the intent validator."""
        return self._intent_validator

    @property
    def intent_history(self) -> 'List[GuardianIntent]':
        """Get the intent history."""
        return list(self._intent_history)

    @property
    def conversation_intent(self) -> 'LiveConversationIntentBridge':
        """Get the conversation intent bridge."""
        return self._conversation_intent

    @property
    def dashboard_intent(self) -> 'LiveDashboardIntentBridgeCls':
        """Get the dashboard intent bridge."""
        return self._dashboard_intent

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
            "registry_count": self._registry.count,
            "registry_runtimes": self._registry.ids,
            "sync_count": self._synchronizer.sync_count,
            "snapshot_count": self._snapshot_manager.count,
            "consistent": self._validator.is_consistent(),
            "transition_count": self._timeline.count,
            "critical_transitions": self._timeline.get_summary().critical_count,
            "situation_count": self._situation_history.count,
            "current_situation": (
                self._situation_history.latest.situation_type.name
                if self._situation_history.latest else None
            ),
            "current_severity": (
                self._situation_history.latest.severity.name
                if self._situation_history.latest else None
            ),
            "assessment_count": len(self._assessment_history),
            "current_risk": (
                self._assessment_history[-1].risk.name
                if self._assessment_history else None
            ),
            "current_priority": (
                self._assessment_history[-1].priority.name
                if self._assessment_history else None
            ),
            "intent_count": len(self._intent_history),
            "current_intent": (
                self._intent_history[-1].intent_type.name
                if self._intent_history else None
            ),
        }

    # --- Pipeline Execution ---

    def execute_pipeline(
        self,
        observation_payload: Optional[object] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full live pipeline.

        Pipeline (v5.2.0):
            1. Create observation event
            2. Dispatch to guardian
            3. Synchronization
            4. Transition Intelligence
            5. Reasoning
            6. Learning
            7. Execution Preview
            8. Dashboard refresh
            9. Conversation update
            10. Return pipeline result

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

        sync_result = None
        transition_result = None
        reasoning_result = None
        learning_result = None
        execution_result = None

        # Step 3: Record in history
        if snapshot:
            self.record_dispatch(
                event=event,
                processing_ms=snapshot.duration_ms,
                subscriber_count=len(self._dispatcher.subscribers),
                error_count=len(snapshot.errors),
            )

            if not snapshot.errors:
                # 3a. Synchronization
                sync_result = self._synchronizer.synchronize(event)

                # 3b. Capture registry snapshot
                registry_snapshot = self._registry.snapshot()
                self._snapshot_manager.capture(registry_snapshot)

                # 3c. Transition Intelligence (NEW v5.2.0)
                if self._snapshot_manager.count >= 2:
                    snaps = self._snapshot_manager.history
                    transitions = self._change_detector.detect(
                        snaps[-2], snaps[-1]
                    )
                    self._timeline.record_batch(transitions)
                    impact_result = self._impact_analyzer.analyze_batch(transitions)

                    # Registry change detection
                    current_count = self._registry.count
                    reg_transition = self._change_detector.detect_registry_change(
                        self._last_registry_count, current_count
                    )
                    if reg_transition:
                        self._timeline.record(reg_transition)
                    self._last_registry_count = current_count

                    transition_result = {
                        "transitions_found": len(transitions),
                        "impact": impact_result,
                        "total_in_timeline": self._timeline.count,
                    }

                    # 3d. Situation Intelligence (NEW v5.3.0)
                    if transitions:
                        situations = self._classifier.classify(transitions)
                        self._situation_history.record_batch(situations)
                        transition_result["situations_found"] = len(situations)

                        # 3e. Operational Assessment (NEW v5.4.0)
                        assessment_result = []
                        for sit in situations:
                            a = self._assessment_builder.build_from_situation(
                                sit, transitions
                            )
                            self._assessment_history.append(a)
                            assessment_result.append({
                                "assessment_id": a.assessment_id,
                                "level": a.level.name,
                                "risk": a.risk.name,
                                "priority": a.priority.name,
                                "confidence": a.confidence,
                            })
                        transition_result["assessments"] = assessment_result

                        # 3f. Operational Intent (NEW v5.5.0)
                        intent_result = []
                        for a_obj in [self._assessment_builder.build_from_situation(sit, transitions) for sit in situations]:
                            intent = self._intent_builder.build_from_assessment(a_obj)
                            policy_result = self._intent_policy.apply_policy(intent)
                            validation = self._intent_validator.validate(intent, self._intent_history)
                            self._intent_history.append(intent)
                            intent_result.append({
                                "intent_id": intent.intent_id,
                                "type": intent.intent_type.name,
                                "priority": intent.priority.name,
                                "policy": intent.policy_name,
                                "policy_action": policy_result["result"],
                                "valid": validation.valid,
                            })
                        transition_result["intents"] = intent_result

                # 4. Reasoning
                reasoning_result = self._reasoning.trigger(event)
                # 5. Learning
                learning_result = self._learning.feed(event)
                # 6. Execution Preview
                execution_result = self._execution.preview(event)
                # 7. Dashboard refresh
                self._dashboard.refresh()
                # 8. Conversation update
                self._conversation.update()

        return {
            "event_id": event.event_id,
            "snapshot": snapshot.to_dict() if snapshot else None,
            "pipeline": {
                "synchronization": sync_result,
                "transition_intelligence": transition_result,
                "reasoning": reasoning_result,
                "learning": learning_result,
                "execution_preview": execution_result,
            } if snapshot and not snapshot.errors else None,
            "is_running": self._is_running,
            "registry_count": self._registry.count,
            "snapshot_count": self._snapshot_manager.count,
            "transition_count": self._timeline.count,
            "situation_count": self._situation_history.count,
            "intent_count": len(self._intent_history),
        }
