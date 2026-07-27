# Compatibility shim for legacy CLI
__all__ = ["HistoryEngine"]


class HistoryEngine:
    """Minimal stubbed engine for legacy CLI imports."""

    def __init__(self, telemetry=None):
        self.telemetry = telemetry

    def get_recent_events(self, limit: int = 10) -> list:
        return []

    def get_timeline(self) -> list:
        return []
