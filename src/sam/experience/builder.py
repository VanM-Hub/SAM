"""
Experience Builder — merakit ViewModel dari berbagai engine.
"""

import structlog
from typing import Optional

from ..telemetry.service import TelemetryService

logger = structlog.get_logger()


class ExperienceBuilder:
    """Builder untuk merakit data dari berbagai engine menjadi ViewModel."""

    def __init__(self, telemetry: TelemetryService):
        self.telemetry = telemetry

    def build_home(self):
        """Build HomeModel from current state."""
        from ..experience.pages.home import HomeModel, HomeStatus
        from ..operations.engine.context import ContextEngine
        from ..operations.engine.status import StatusEngine

        context = ContextEngine().get_context()
        status_engine = StatusEngine(self.telemetry)

        status = status_engine.get_status()
        health_score = status_engine.get_health_score()
        recent_changes = status_engine.get_recent_changes()

        # Simulasi data tambahan (nanti dari engine lain)
        active_tasks = 0
        pending_approvals = 0
        pending_tasks = 0
        recommendations = []
        needs_attention = status not in [HomeStatus.HEALTHY, HomeStatus.BUSY]

        # Uptime
        uptime = "2h 14m"  # nanti dari Runtime

        return HomeModel(
            status=status,
            status_message=status_engine.get_status_message(),
            system_health=health_score,
            mission_name=context.mission_name,
            mission_health=health_score,
            current_activity="Monitoring runtime",
            active_tasks=active_tasks,
            recent_changes=recent_changes,
            needs_attention=needs_attention,
            pending_approvals=pending_approvals,
            pending_tasks=pending_tasks,
            recommendations=recommendations,
            uptime=uptime,
            operator_name=context.operator,
        )
