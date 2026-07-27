# Compatibility shim — TelemetrySeverity was in sam.telemetry.models
# which is no longer present. Re-export from the canonical event module.
from .event import EventSeverity as TelemetrySeverity  # noqa: F401

__all__ = ["TelemetrySeverity"]
