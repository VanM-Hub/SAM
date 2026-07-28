"""ConsoleIntegration — Connects Conversation API to Console via Presentation Layer.

Pipeline: Conversation API → DTO → DashboardComposer → ConsoleSession → Renderer

This is the ONLY file that bridges domain/operations code with presentation code.
It ensures the pipeline is enforced: NO bypassing layers.
"""

from __future__ import annotations
from typing import Any, Callable, Optional, Tuple
from dataclasses import dataclass, field

from ..dashboard_model import MissionDashboardDTO
from ..action_center import ActionCenterDTO
from ..notification import Notification, NotificationStore
from ..summary_builder import OperationalSummary
from ..conversation_api import Conversation, SAM

from .dashboard_composer import ConsoleDashboard, DashboardComposer
from .console_session import ConsoleSession
from .console_renderer import ConsoleRenderer
from .navigation_runtime import NavigationRuntime
from .live_refresh import LiveRefresh
from .dispatcher import CommandDispatcher
from .theme_runtime import ThemeRuntime
from .widgets import WidgetRegistry


@dataclass
class ConsoleIntegration:
    """Bridge between Conversation API and Console Presentation Layer.

    Pipeline:
        Conversation API → DTO → DashboardComposer → ConsoleSession → Renderer

    This integration ensures:
    - No bypass of the pipeline
    - No direct domain access from presentation
    - All data flows through DTOs
    - No business logic in presentation

    Usage:
        sam = SAM()
        integration = ConsoleIntegration(sam)
        integration.initialize()
        integration.render_current()
    """

    sam: Any  # SAM instance
    conversation: Optional[Conversation] = None

    session: ConsoleSession = field(default_factory=ConsoleSession)
    composer: DashboardComposer = field(default_factory=DashboardComposer)
    notification_store: NotificationStore = field(default_factory=NotificationStore)

    _initialized: bool = False
    _last_dashboard_min: ConsoleDashboard = field(default_factory=ConsoleDashboard)

    def initialize(self) -> None:
        """Initialize the console integration.

        Starts a conversation session and wires up the dispatcher.
        """
        if self._initialized:
            return

        # Start a conversation
        self.conversation = self.sam.observe(audience_type="administrator")

        # Wire dispatcher to conversation handler
        self.session.dispatcher.set_handler(self._conversation_handler)

        # Start session
        self.session.start()
        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    # ── Data flow ─────────────────────────────────────────────────────

    def refresh_dashboard(self) -> ConsoleDashboard:
        """Full pipeline: Conversation → DTO → Composer → Dashboard."""
        if not self.conversation:
            return ConsoleDashboard()

        dto = self._fetch_dashboard_dto()
        action_dto = self._fetch_action_dto()
        notifications = self.notification_store.all()
        summary = self._fetch_summary()

        dashboard = self.composer.compose(
            mission_dto=dto,
            action_dto=action_dto,
            notification_store=notifications,
            summary=summary,
        )

        self._last_dashboard_min = dashboard
        self.session.update_dashboard(dashboard)
        return dashboard

    def render_current(self) -> None:
        """Refresh dashboard data and render the current screen."""
        if not self._initialized:
            return

        self.refresh_dashboard()
        self.session.render()

    def send_query(self, text: str) -> str:
        """Send a natural language query to SAM.

        Returns the answer text.
        """
        if not self.conversation:
            return "No active conversation."

        try:
            answer = self.conversation.answer(text)
            return str(answer)
        except Exception as e:
            return f"Error: {e}"

    # ── Notifications ─────────────────────────────────────────────────

    def push_notification(self, notification: Notification) -> None:
        """Push a notification and update dashboard."""
        self.notification_store.push(notification)
        self.session.refresh.on_notification()

    def acknowledge_notifications(self) -> int:
        """Acknowledge all unread notifications."""
        return self.notification_store.acknowledge_all()

    # ── Navigation ────────────────────────────────────────────────────

    def navigate_to(self, screen: str) -> bool:
        """Navigate to a specific screen."""
        return self.session.navigate_to(screen)

    def go_home(self) -> None:
        self.session.go_home()

    def go_back(self) -> bool:
        return self.session.go_back()

    # ── Theme ─────────────────────────────────────────────────────────

    def set_theme(self, name: str) -> bool:
        return self.session.set_theme(name)

    def cycle_theme(self) -> str:
        return self.session.cycle_theme()

    # ── Input ─────────────────────────────────────────────────────────

    def handle_input(self, line: str) -> Any:
        """Handle user input line."""
        result = self.session.handle_input(line)
        if result.success and result.message:
            self.session.render()
        return result

    # ── Lifecycle ─────────────────────────────────────────────────────

    def tick(self, seconds_since_last: float = 0.0) -> None:
        """Periodic tick handler."""
        if self._initialized:
            self.session.tick(seconds_since_last)

    def shutdown(self) -> None:
        """Shutdown the console integration."""
        self.session.stop()
        self._initialized = False

    # ── Internal pipeline ─────────────────────────────────────────────

    def _fetch_dashboard_dto(self) -> MissionDashboardDTO:
        """Fetch MissionDashboardDTO from Conversation API."""
        if not self.conversation:
            return MissionDashboardDTO()

        try:
            co = self.conversation._co
            total_m = getattr(co, "activity_count", 0) or 0
            pending_a = getattr(co, "approval_pending_count", 0) or 0
            from ..mission_query import MissionQueryEngine
            mqe = MissionQueryEngine(self.conversation)
            mission_data = mqe.summary()

            return MissionDashboardDTO(
                mission_stats=self._make_stat_summary(total=total_m),
                health=self._make_health_summary(),
                trust=self._make_trust_summary(),
                scheduler=self._make_scheduler_status(),
            )
        except Exception:
            return MissionDashboardDTO()

    @staticmethod
    def _make_stat_summary(total: int = 0):
        from ..dashboard_model import MissionStatSummary
        return MissionStatSummary(total=total)

    @staticmethod
    def _make_health_summary():
        from ..dashboard_model import HealthSummary
        return HealthSummary(overall="unknown")

    @staticmethod
    def _make_trust_summary():
        from ..dashboard_model import TrustSummary
        return TrustSummary()

    @staticmethod
    def _make_scheduler_status():
        from ..dashboard_model import SchedulerStatus
        return SchedulerStatus()

    def _fetch_action_dto(self) -> ActionCenterDTO:
        """Fetch ActionCenterDTO from Conversation API."""
        if not self.conversation:
            return ActionCenterDTO()

        try:
            co = self.conversation._co
            pending_approvals_list: list = []
            pending_a = getattr(co, "approval_pending_count", 0) or 0
            actions = getattr(co, "user_actions", [])
            if pending_a:
                from ..action_center import ActionCenterItem
                pending_approvals_list.append(ActionCenterItem(
                    id="dash", kind="approval", title=f"{pending_a} pending approvals",
                    status="pending", risk="normal",
                ))
            pending_missions_list: list = []
            for i, act in enumerate(actions[:5]):
                from ..action_center import ActionCenterItem
                pending_missions_list.append(ActionCenterItem(
                    id=f"act_{i}", kind="alert", title=str(act),
                    status="pending", risk="normal", priority=i,
                ))
            from ..action_center import ActionCenterDTO
            return ActionCenterDTO(
                pending_approvals=pending_approvals_list,
                pending_missions=pending_missions_list,
                total_pending=pending_a + len(actions),
                total_high_risk=0,
            )
        except Exception:
            return ActionCenterDTO()

    def _fetch_summary(self) -> OperationalSummary:
        """Fetch operational summary from Conversation API."""
        if not self.conversation:
            return OperationalSummary()

        try:
            co = self.conversation._co
            return OperationalSummary(
                mission_name=getattr(co, "mission_target", ""),
                mission_state=getattr(co, "mission_condition", ""),
                problem=getattr(co, "situation_summary", ""),
                decision_taken=getattr(co, "sam_decision", ""),
                decision_confidence=getattr(co, "sam_confidence", 0.0) or 0.0,
            )
        except Exception:
            return OperationalSummary()

    def _conversation_handler(self, interaction: Any) -> Optional[str]:
        """Handler for processing Interaction Contract objects.

        Called by CommandDispatcher.
        Converts Interaction Contract objects to Conversation API calls.
        """
        if not self.conversation:
            return "No active conversation."

        from .interaction import (
            ApproveMission, RejectMission, CancelMission, ResumeMission,
            ExecuteRecommendation, SimulateRecommendation,
            OpenMission, OpenTimeline, OpenEvidence,
            RefreshDashboard, UserQuery,
        )

        try:
            if isinstance(interaction, ApproveMission):
                self.conversation.answer(f"approve {interaction.mission_id}")
                return f"Approved mission {interaction.mission_id}"

            elif isinstance(interaction, RejectMission):
                self.conversation.answer(f"reject {interaction.mission_id}")
                return f"Rejected mission {interaction.mission_id}"

            elif isinstance(interaction, CancelMission):
                self.conversation.answer(f"cancel {interaction.mission_id}")
                return f"Cancelled mission {interaction.mission_id}"

            elif isinstance(interaction, ResumeMission):
                self.conversation.answer(f"resume {interaction.mission_id}")
                return f"Resumed mission {interaction.mission_id}"

            elif isinstance(interaction, RefreshDashboard):
                self.refresh_dashboard()
                return "Dashboard refreshed."

            elif isinstance(interaction, UserQuery):
                return str(self.conversation.answer(interaction.text))

            else:
                return f"Unhandled interaction: {type(interaction).__name__}"

        except Exception as e:
            return f"Error: {e}"
