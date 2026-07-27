"""
Knowledge Engine — membaca knowledge dari telemetry dan Knowledge Store.
"""

import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...telemetry.service import TelemetryService
from ...experience.models.knowledge import KnowledgeEntry, KnowledgeModel, KnowledgeType, InsightEntry

logger = structlog.get_logger()


class KnowledgeEngine:
    """Engine untuk knowledge dan rekomendasi."""

    def __init__(self, telemetry, knowledge_store=None):
        self.telemetry = telemetry
        self.knowledge_store = knowledge_store

    def get_knowledge(self):
        """Get all knowledge entries."""
        entries = []

        # 1. Dari telemetry recommendations
        rec_events = self.telemetry.query({})
        rec_events = [e for e in rec_events if "recommendation" in e.type.value]
        for e in rec_events[:20]:
            title = e.message[:50] if e.message else "Recommendation"
            entries.append(KnowledgeEntry(
                id=e.id,
                type=KnowledgeType.RECOMMENDATION,
                title=title,
                content=e.message or "",
                confidence=0.7,
                source="telemetry",
                timestamp=e.timestamp,
                tags=["auto-generated"],
            ))

        # 2. Dari telemetry patterns (guardian alerts)
        alert_events = [e for e in self.telemetry.query({}) if "guardian" in e.type.value]
        for e in alert_events[:10]:
            entries.append(KnowledgeEntry(
                id=e.id,
                type=KnowledgeType.PATTERN,
                title="Pattern: {}".format(e.message[:40] if e.message else "detected"),
                content=e.message or "",
                confidence=0.6,
                source="telemetry",
                timestamp=e.timestamp,
                tags=["detected"],
            ))

        # 3. Dari telemetry lessons (task failures → lessons learned)
        failed_events = [e for e in self.telemetry.query({}) if "failed" in e.type.value]
        for e in failed_events[:5]:
            entries.append(KnowledgeEntry(
                id=e.id,
                type=KnowledgeType.LESSON,
                title="Lesson: {}".format(e.message[:40] if e.message else "failure"),
                content=e.message or "",
                confidence=0.5,
                source="telemetry",
                timestamp=e.timestamp,
                tags=["learned"],
            ))

        # 4. Insights
        insights = self._build_insights()

        return KnowledgeModel(
            entries=entries,
            insights=insights,
            total_entries=len(entries),
        )

    def search(self, query):
        """Search knowledge entries by query."""
        model = self.get_knowledge()
        query_lower = query.lower()
        results = []
        for entry in model.entries:
            if query_lower in entry.title.lower() or query_lower in entry.content.lower():
                results.append(entry)
        return results

    def get_recommendations(self):
        """Get only recommendations."""
        model = self.get_knowledge()
        return [e for e in model.entries if e.type == KnowledgeType.RECOMMENDATION]

    def _build_insights(self):
        """Build insights from patterns."""
        insights = []

        # Insight 1: Repeated failures
        failed_events = [e for e in self.telemetry.query({})
                         if e.severity.value in ["error", "critical"]]
        if len(failed_events) > 5:
            components = {}
            for e in failed_events:
                comp = e.component.value
                components[comp] = components.get(comp, 0) + 1

            top_component = max(components, key=components.get)
            if components.get(top_component, 0) > 3:
                insights.append(InsightEntry(
                    id="insight_001",
                    title="Repeated failures detected",
                    description="Component '{}' has failed {} times recently.".format(
                        top_component, components[top_component]
                    ),
                    severity="warning",
                    evidence=["{}: {} failures".format(top_component, components[top_component])],
                    created_at=datetime.utcnow(),
                ))

        # Insight 2: High recovery activity
        recover_events = [e for e in self.telemetry.query({}) if "recover" in e.type.value]
        if len(recover_events) > 3:
            insights.append(InsightEntry(
                id="insight_002",
                title="Frequent recovery activity",
                description="SAM has recovered {} times recently. This may indicate instability.".format(
                    len(recover_events)
                ),
                severity="warning",
                evidence=["{} recovery events".format(len(recover_events))],
                created_at=datetime.utcnow(),
            ))

        # Insight 3: Steady operations (no insight_003 tanpa knowledge_store untuk sekarang)
        all_events = self.telemetry.query({})
        if len(all_events) > 50:
            insights.append(InsightEntry(
                id="insight_003",
                title="System is operational",
                description="SAM has processed {} events. Operations are steady.".format(
                    len(all_events)
                ),
                severity="info",
                evidence=["{} total events".format(len(all_events))],
                created_at=datetime.utcnow(),
            ))

        return insights
