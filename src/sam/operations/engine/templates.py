"""
Explanation Templates — template-based explanation generator.
"""

from typing import Dict, Any


TEMPLATES = {
    "task.failed": {
        "title": "Task failed: {task_name}",
        "why": "Task failed because {reason}.",
        "impact": "Task execution halted.",
        "recommendation": "{recommendation_description}",
        "severity": "error",
    },
    "task.completed": {
        "title": "Task completed: {task_name}",
        "why": "Task completed successfully.",
        "impact": "No impact.",
        "recommendation": "No action required.",
        "severity": "info",
    },
    "runtime.recovering": {
        "title": "Recovery started: {target}",
        "why": "Recovery triggered because {reason}.",
        "impact": "System entering recovery mode.",
        "recommendation": "Monitor recovery progress.",
        "severity": "warning",
    },
    "runtime.started": {
        "title": "Runtime started",
        "why": "SAM runtime initialized successfully.",
        "impact": "System is now operational.",
        "recommendation": "No action required.",
        "severity": "info",
    },
    "component.degraded": {
        "title": "Component degraded: {component_name}",
        "why": "Component degraded because {reason}.",
        "impact": "Performance may be affected.",
        "recommendation": "Monitor component health.",
        "severity": "warning",
    },
    "component.failed": {
        "title": "Component failed: {component_name}",
        "why": "Component failed because {reason}.",
        "impact": "Service may be unavailable.",
        "recommendation": "Restart component or investigate logs.",
        "severity": "error",
    },
    "guardian.alert": {
        "title": "Guardian alert: {alert_name}",
        "why": "Alert triggered because {reason}.",
        "impact": "Attention required.",
        "recommendation": "Investigate the alert.",
        "severity": "warning",
    },
    "default": {
        "title": "Event: {event_name}",
        "why": "Event occurred: {reason}.",
        "impact": "Impact unknown.",
        "recommendation": "Investigate the event.",
        "severity": "info",
    },
}


class ExplanationTemplates:
    """Template-based explanation generator."""

    @staticmethod
    def get_template(event_type):
        """Get template for event type."""
        return TEMPLATES.get(event_type, TEMPLATES.get("default", {}))
