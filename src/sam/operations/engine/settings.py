# Compatibility shim for legacy CLI
"""Settings Engine — minimal stub for legacy CLI imports."""

from dataclasses import dataclass


class SettingsEngine:
    """Minimal stubbed engine for legacy CLI imports."""

    def __init__(self, telemetry=None):
        self.telemetry = telemetry

    def get_settings(self) -> dict:
        return {
            "runtime": {"version": "4.0.0", "state": "ready"},
            "telemetry": {"enabled": True, "max_events": 1000},
            "openclaw": {"enabled": False, "workspace": None},
        }
