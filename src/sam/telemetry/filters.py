from typing import List, Dict, Any

from .event import TelemetryEvent


class Filter:
    @staticmethod
    def apply(events: List[TelemetryEvent], filters: Dict[str, Any]) -> List[TelemetryEvent]:
        result = events

        # Filter by severity
        if "severity" in filters:
            severity = filters["severity"]
            if isinstance(severity, str):
                result = [e for e in result if e.severity.value == severity]
            elif isinstance(severity, list):
                result = [e for e in result if e.severity.value in severity]

        # Filter by component
        if "component" in filters:
            comp = filters["component"]
            if isinstance(comp, str):
                result = [e for e in result if e.component.value == comp]
            elif isinstance(comp, list):
                result = [e for e in result if e.component.value in comp]

        # Filter by category
        if "category" in filters:
            cat = filters["category"]
            if isinstance(cat, str):
                result = [e for e in result if e.category.value == cat]
            elif isinstance(cat, list):
                result = [e for e in result if e.category.value in cat]

        # Filter by time range
        if "from" in filters:
            from_time = filters["from"]
            result = [e for e in result if e.timestamp >= from_time]

        if "to" in filters:
            to_time = filters["to"]
            result = [e for e in result if e.timestamp <= to_time]

        return result
