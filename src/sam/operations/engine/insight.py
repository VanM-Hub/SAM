"""
Insight Engine — insight yang muncul dari pola aktivitas.
"""

from typing import List
from ...telemetry.service import TelemetryService
from ...experience.models.knowledge import InsightEntry


class InsightEngine:
    """Engine untuk menghasilkan insight dari telemetry."""

    def __init__(self, telemetry):
        self.telemetry = telemetry

    def generate_insights(self):
        """Generate insights from telemetry patterns."""
        # Re-use dari KnowledgeEngine._build_insights
        from .knowledge import KnowledgeEngine
        return KnowledgeEngine(self.telemetry)._build_insights()
