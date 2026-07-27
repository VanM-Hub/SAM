# Compatibility shim for legacy CLI
"""Task Engine — minimal stub for legacy CLI imports."""

from typing import List


class TaskEngine:
    """Minimal stubbed engine for legacy CLI imports."""

    def __init__(self, telemetry=None):
        self.telemetry = telemetry

    def list_tasks(self) -> List[dict]:
        return []

    def get_task(self, task_id: str) -> dict:
        return {"id": task_id, "status": "unknown", "created": ""}
