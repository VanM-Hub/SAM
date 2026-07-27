"""
Explainability Engine — template-based explanation generator (bukan LLM).
"""

import structlog
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from ...telemetry.service import TelemetryService
from ...experience.models.explain import (
    Explanation, Evidence, Impact, Recommendation, ExplanationSeverity,
)
from .templates import ExplanationTemplates

logger = structlog.get_logger()


class ExplainabilityEngine:
    """Engine untuk menghasilkan penjelasan deterministik."""

    def __init__(self, telemetry):
        self.telemetry = telemetry

    def explain_event(self, event_id):
        """Generate explanation for an event."""
        events = self.telemetry.query({})
        event = None
        for e in events:
            if e.id == event_id:
                event = e
                break

        if not event:
            logger.warning("event_not_found", event_id=event_id)
            return None

        return self._build_explanation(event)

    def explain_task(self, task_id):
        """Generate explanation for a task."""
        events = self.telemetry.query({})
        task_events = [
            e for e in events
            if e.workflow_id == task_id or e.correlation_id == task_id
        ]

        if not task_events:
            logger.warning("task_events_not_found", task_id=task_id)
            return None

        last_event = task_events[-1]
        return self._build_explanation(last_event, task_events=task_events)

    def explain_recent(self, limit=10):
        """Generate explanations for recent events."""
        events = self.telemetry.get_recent(limit=limit)
        explanations = []
        for e in events:
            expl = self._build_explanation(e)
            if expl:
                explanations.append(expl)
        return explanations

    def _build_explanation(self, event, task_events=None):
        """Build explanation from event and templates."""
        template = ExplanationTemplates.get_template(event.type.value)

        # Extract context
        context = self._extract_context(event, task_events)

        # Format template
        # Merge explicit kwargs with context; context wins for overlap
        format_kwargs = {
            "event_name": event.type.value,
            "task_name": "Unknown",
            "component_name": event.component.value,
            "alert_name": "Unknown",
            "target": "Unknown",
        }
        format_kwargs.update(context)
        title = template.get("title", "Event: {event_name}").format(**format_kwargs)

        why_kwargs = {"reason": "Unknown reason"}
        why_kwargs.update(context)
        why = template.get("why", "Event occurred.").format(**why_kwargs)

        impact_desc = template.get("impact", "Impact unknown.").format(**{"impact_description": context.get("impact_description", "Unknown impact"), **context})

        rec_kwargs = {"recommendation_description": context.get("recommendation_description", "No specific recommendation")}
        rec_kwargs.update(context)
        rec_desc = template.get("recommendation", "Investigate the event.").format(**rec_kwargs)

        severity_map = {
            "info": ExplanationSeverity.INFO,
            "warning": ExplanationSeverity.WARNING,
            "error": ExplanationSeverity.ERROR,
            "critical": ExplanationSeverity.CRITICAL,
            "success": ExplanationSeverity.INFO,
        }
        severity = severity_map.get(template.get("severity", "info"), ExplanationSeverity.INFO)

        # Evidence
        evidence = []
        if task_events:
            for e in task_events[:5]:
                evidence.append(Evidence(
                    source=e.id,
                    description=e.message,
                    timestamp=e.timestamp,
                    confidence=0.9,
                ))
        else:
            evidence.append(Evidence(
                source=event.id,
                description=event.message,
                timestamp=event.timestamp,
                confidence=0.8,
            ))

        # Impact
        impact = Impact(
            description=impact_desc,
            severity=severity,
            affected_components=[event.component.value],
        )

        # Recommendation
        recommendation = Recommendation(
            description=rec_desc,
            priority=1,
        )

        return Explanation(
            id=str(uuid.uuid4())[:8],
            title=title,
            description=why,
            severity=severity,
            timestamp=event.timestamp,
            why=why,
            evidence=evidence,
            impact=impact,
            recommendation=recommendation,
            event_id=event.id,
            task_id=event.workflow_id or event.correlation_id,
            correlation_id=event.correlation_id,
            confidence=0.9,
        )

    def _extract_context(self, event, task_events=None):
        """Extract context from event and task events."""
        context = {
            "task_name": "Unknown",
            "reason": "Unknown reason",
            "impact_description": "Unknown impact",
            "recommendation_description": "No specific recommendation",
            "component_name": event.component.value,
            "target": "Unknown",
            "alert_name": "Unknown",
        }

        # Ambil dari metadata event
        if event.metadata:
            for key in ["task_name", "reason", "impact", "recommendation", "target"]:
                if key in event.metadata:
                    context[key] = event.metadata[key]

        # Ambil dari event messages
        if event.message:
            msg = event.message.lower()
            if "error" in msg or "fail" in msg:
                context["reason"] = event.message[:100]
            if "alert" in msg:
                context["alert_name"] = event.message[:40]

        # Dari task_events
        if task_events:
            for e in task_events:
                msg = e.message.lower()
                if "error" in msg or "fail" in msg:
                    context["reason"] = e.message[:100]
                    break
                if "recommend" in msg:
                    context["recommendation_description"] = e.message[:100]

        return context
