"""Window Scheduler — penjadwalan window waktu."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_scheduler import ScheduleWindow


class WindowScheduler:
    """Penjadwal window — preview-only."""

    def __init__(self) -> None:
        self._windows: Dict[str, ScheduleWindow] = {}

    def add(self, window: ScheduleWindow) -> None:
        self._windows[window.window_id] = window

    def get(self, window_id: str) -> ScheduleWindow | None:
        return self._windows.get(window_id)

    def find_by_subsystem(self, subsystem: str) -> List[ScheduleWindow]:
        return [w for w in self._windows.values() if w.subsystem == subsystem]

    def count(self) -> int:
        return len(self._windows)
