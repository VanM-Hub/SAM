# Compatibility shim — legacy names for sam.telemetry.models.
# Canonical definitions moved to .event and .collector during refactor.
# This module re-exports them so old imports keep working.
from .event import EventSeverity as TelemetrySeverity  # noqa: F401
from .event import TelemetryEvent  # noqa: F401
from .event import EventCategory  # noqa: F401
from .collector import RuntimeMetrics  # noqa: F401

__all__ = ["TelemetrySeverity", "TelemetryEvent", "EventCategory", "RuntimeMetrics"]
