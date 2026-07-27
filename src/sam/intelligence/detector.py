"""
Incident Detector — Phase 1

Mendeteksi insiden dari log dan health OpenClaw.
"""

import structlog
import uuid
from typing import List, Optional
from ..openclaw.logs import OpenClawLogAnalyzer
from ..openclaw.health import OpenClawHealthCollector
from .models import Incident, IncidentSeverity

logger = structlog.get_logger()


class IncidentDetector:
    """Detektor insiden — memonitor log dan health untuk mendeteksi masalah."""

    SEVERITY_MAP = {
        "CRITICAL": IncidentSeverity.CRITICAL,
        "FATAL": IncidentSeverity.CRITICAL,
        "ERROR": IncidentSeverity.HIGH,
        "WARNING": IncidentSeverity.MEDIUM,
    }

    def __init__(self, workspace_path: str = "./"):
        self.workspace_path = workspace_path
        self.log_analyzer = OpenClawLogAnalyzer(workspace_path)
        self.health_collector = OpenClawHealthCollector()

    async def detect(self, log_lines: int = 200) -> List[Incident]:
        """Deteksi insiden dari log dan health OpenClaw.

        Args:
            log_lines: Jumlah baris log terakhir yang dianalisis.

        Returns:
            List insiden yang terdeteksi.
        """
        incidents = []

        # 1. Deteksi dari log
        log_issues = await self.log_analyzer.analyze(lines=log_lines)
        for issue in log_issues:
            sev = self.SEVERITY_MAP.get(issue.get("severity", ""), IncidentSeverity.LOW)
            if sev in (IncidentSeverity.CRITICAL, IncidentSeverity.HIGH, IncidentSeverity.MEDIUM):
                incidents.append(
                    Incident(
                        title=self._summarize(issue["message"], 60),
                        description=issue["message"][:500],
                        severity=sev,
                        source="log:" + issue.get("severity", "unknown").lower(),
                        evidence=[issue],
                    )
                )

        # 2. Deteksi dari health
        try:
            health = await self.health_collector.collect(self.workspace_path)
            for comp in health.components:
                if comp.status.value in ("unhealthy", "degraded"):
                    sev = IncidentSeverity.HIGH if comp.status.value == "unhealthy" else IncidentSeverity.MEDIUM
                    msg = comp.message or "{0} is {1}".format(comp.name, comp.status.value)
                    incidents.append(
                        Incident(
                            title="{0} is {1}".format(comp.name, comp.status.value),
                            description=msg,
                            severity=sev,
                            source="openclaw.health",
                            evidence=[{"component": comp.name, "status": comp.status.value, "message": comp.message}],
                        )
                    )
        except Exception as e:
            logger.warning("health_check_failed_during_detection", error=str(e))

        logger.info("incident_detection_completed", count=len(incidents))
        return incidents

    def _summarize(self, message: str, max_len: int = 60) -> str:
        """Buat ringkasan dari pesan yang panjang."""
        if len(message) <= max_len:
            return message
        return message[:max_len].rsplit(" ", 1)[0] + "..."
