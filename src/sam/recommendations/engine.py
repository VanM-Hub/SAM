"""Recommendation Engine for SAM Framework.

Listens to PatternDetected events and generates actionable recommendations.
"""

import structlog
from typing import List, Dict, Any, Optional
from sam.events import EventBus, Event
from sam.recommendations.models import (
    Recommendation,
    RecommendationSeverity,
    RecommendationStatus,
)

logger = structlog.get_logger()


class RecommendationEngine:
    """Engine that generates recommendations from pattern detections.

    Optionally persists recommendations via a repository implementing add(rec).
    """

    def __init__(self, event_bus: EventBus, repo: Optional[Any] = None) -> None:
        self._recommendations: List[Recommendation] = []
        self._rule_action_map: Dict[str, Dict[str, Any]] = {}
        self._event_bus = event_bus
        self._repo = repo
        self._subscribed = False

        # Subscribe to pattern detection events
        self._subscribe()

    def _subscribe(self) -> None:
        """Subscribe to PatternDetected events on the event bus."""
        if not self._subscribed:
            self._event_bus.subscribe("PatternDetected", self._handle_pattern_detected)
            self._subscribed = True
            logger.info("RecommendationEngine subscribed to PatternDetected events")

    async def _handle_pattern_detected(self, event: Event) -> None:
        """Handle a PatternDetected event and generate a recommendation."""
        payload = event.payload or {}
        rule_id = payload.get("rule_id")
        detection_id = payload.get("detection_id")
        severity = payload.get("severity", "info")
        message = payload.get("message", "")
        knowledge_fact_ids = payload.get("knowledge_fact_ids", [])
        execution_id = payload.get("execution_id")
        # Get correlation_id from event payload (top level, not metadata)
        correlation_id = payload.get("correlation_id")
        metadata = payload.get("metadata", {})

        if not rule_id or not detection_id:
            logger.warning(
                "PatternDetected event missing required fields",
                rule_id=rule_id,
                detection_id=detection_id,
            )
            return

        # Look up recommendation template for this rule
        template = self._rule_action_map.get(rule_id)
        if not template:
            logger.debug(
                "No recommendation template for rule",
                rule_id=rule_id,
            )
            return

        # Create recommendation
        recommendation = Recommendation(
            rule_id=rule_id,
            pattern_detection_id=detection_id,
            severity=RecommendationSeverity(template.get("severity", "info")),
            title=template.get("title", f"Recommendation for {rule_id}"),
            description=template.get("description", message),
            action_hint=template.get("action_hint", "Review and take appropriate action"),
            status=RecommendationStatus.ACTIVE,
            metadata={
                **metadata,
                "knowledge_fact_ids": knowledge_fact_ids,
                "execution_id": execution_id,
                "correlation_id": correlation_id,
            },
        )

        self._recommendations.append(recommendation)

        # Persist if repository provided
        if self._repo is not None:
            try:
                await self._repo.add(recommendation, correlation_id=correlation_id)
            except Exception:
                logger.exception("Failed to persist recommendation", recommendation_id=recommendation.id)


        # Publish RecommendationGenerated event
        await self._event_bus.publish(Event(
            type="RecommendationGenerated",
            source="recommendation_engine",
            payload={
                "recommendation_id": recommendation.id,
                "rule_id": recommendation.rule_id,
                "pattern_detection_id": recommendation.pattern_detection_id,
                "severity": recommendation.severity.value,
                "title": recommendation.title,
                "description": recommendation.description,
                "action_hint": recommendation.action_hint,
                "status": recommendation.status.value,
                "timestamp": recommendation.timestamp.isoformat(),
                "metadata": recommendation.metadata,
            },
        ))

        logger.info(
            "Recommendation generated",
            recommendation_id=recommendation.id,
            rule_id=rule_id,
            severity=recommendation.severity.value,
            title=recommendation.title,
        )

    async def register_rule_action(self, rule_id: str, template: Dict[str, Any]) -> None:
        """Register a recommendation template for a rule.

        Args:
            rule_id: The pattern rule ID to map.
            template: Dictionary with keys: severity, title, description, action_hint
        """
        self._rule_action_map[rule_id] = template
        logger.info(
            "Recommendation template registered",
            rule_id=rule_id,
            title=template.get("title"),
            severity=template.get("severity"),
        )

    async def get_recommendations(self, limit: int = 100) -> List[Recommendation]:
        """Get recent recommendations, most recent first.

        Args:
            limit: Maximum number of recommendations to return.

        Returns:
            List of Recommendation objects.
        """
        sorted_recs = sorted(self._recommendations, key=lambda r: r.timestamp, reverse=True)
        return sorted_recs[:limit]

    async def update_status(
        self,
        recommendation_id: str,
        status: RecommendationStatus
    ) -> bool:
        """Update the status of a recommendation.

        Args:
            recommendation_id: The recommendation ID to update.
            status: New status to set.

        Returns:
            True if found and updated, False if not found.
        """
        for rec in self._recommendations:
            if rec.id == recommendation_id:
                rec.status = status
                logger.info(
                    "Recommendation status updated",
                    recommendation_id=recommendation_id,
                    new_status=status.value,
                )
                if self._repo is not None:
                    try:
                        await self._repo.add(rec)
                    except Exception:
                        logger.exception("Failed to persist recommendation status update", recommendation_id=recommendation_id)
                return True
        return False

    async def clear(self) -> None:
        """Clear all recommendations and rule mappings. Primarily for testing."""
        count = len(self._recommendations)
        rule_count = len(self._rule_action_map)
        self._recommendations.clear()
        self._rule_action_map.clear()
        logger.info("RecommendationEngine cleared", recommendations=count, rules=rule_count)