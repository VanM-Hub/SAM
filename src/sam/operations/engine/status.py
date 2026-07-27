import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from ...experience.pages.home import HomeStatus
from ...telemetry.service import TelemetryService

logger = structlog.get_logger()


class StatusEngine:
    """Engine untuk menentukan status sistem."""

    def __init__(self, telemetry: TelemetryService):
        self.telemetry = telemetry
        self._last_status = HomeStatus.HEALTHY
        self._status_message = "Everything is healthy"

    def get_status(self) -> HomeStatus:
        """Get current system status based on recent events."""
        # Ambil event 5 menit terakhir
        recent = self.telemetry.query({
            "from": datetime.utcnow() - timedelta(minutes=5)
        })

        # Cek critical errors
        errors = [e for e in recent if e.severity.value == "critical"]
        if errors:
            self._last_status = HomeStatus.UNHEALTHY
            self._status_message = "Critical: {}".format(errors[-1].message[:100])
            return self._last_status

        # Cek errors
        warnings = [e for e in recent if e.severity.value == "error"]
        if warnings:
            self._last_status = HomeStatus.DEGRADED
            self._status_message = "Degraded: {}".format(warnings[-1].message[:100])
            return self._last_status

        # Cek recovering
        recovery_events = [e for e in recent if "recover" in e.type.value]
        if recovery_events:
            self._last_status = HomeStatus.RECOVERING
            self._status_message = "System is recovering..."
            return self._last_status

        # Cek learning
        learning_events = [
            e for e in recent
            if "knowledge" in e.type.value or "memory" in e.type.value
        ]
        if learning_events and len(learning_events) > 3:
            self._last_status = HomeStatus.LEARNING
            self._status_message = "System is learning..."
            return self._last_status

        # Cek busy
        task_events = [e for e in recent if "task" in e.type.value]
        if len(task_events) > 10:
            self._last_status = HomeStatus.BUSY
            self._status_message = "System is busy..."
            return self._last_status

        # Default: healthy
        self._last_status = HomeStatus.HEALTHY
        self._status_message = "Everything is healthy"
        return self._last_status

    def get_health_score(self) -> float:
        """Calculate health score (0-100)."""
        status = self.get_status()
        if status == HomeStatus.HEALTHY:
            return 100.0
        elif status == HomeStatus.BUSY:
            return 85.0
        elif status == HomeStatus.LEARNING:
            return 80.0
        elif status == HomeStatus.RECOVERING:
            return 60.0
        elif status == HomeStatus.DEGRADED:
            return 40.0
        elif status == HomeStatus.UNHEALTHY:
            return 10.0
        return 50.0

    def get_status_message(self) -> str:
        """Get human-readable status message."""
        return self._status_message

    def get_recent_changes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent significant changes."""
        events = self.telemetry.get_recent(limit=20)
        significant = [
            e for e in events
            if e.severity.value in ["warning", "error", "critical"]
            or e.type.value.startswith("task.completed")
            or e.type.value.startswith("task.failed")
            or e.type.value.startswith("plugin.installed")
        ]
        return [
            {
                "message": e.to_human(),
                "timestamp": e.timestamp.isoformat(),
                "type": e.type.value,
                "severity": e.severity.value,
            }
            for e in significant[:limit]
        ]
