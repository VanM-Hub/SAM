"""Sync Coordinator — koordinator sinkronisasi."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_coordinator import SyncPoint


class SyncCoordinator:
    """Koordinator sinkronisasi — preview-only."""

    def __init__(self) -> None:
        self._points: Dict[str, SyncPoint] = {}

    def register(self, point: SyncPoint) -> None:
        self._points[point.sync_id] = point

    def get(self, sync_id: str) -> SyncPoint | None:
        return self._points.get(sync_id)

    def mark_synced(self, sync_id: str, data: str = "") -> SyncPoint | None:
        point = self._points.get(sync_id)
        if not point:
            return None
        p2 = SyncPoint(sync_id, point.subsystem, True, data or point.data)
        self._points[sync_id] = p2
        return p2

    def list_unsynced(self) -> List[SyncPoint]:
        return [p for p in self._points.values() if not p.synced]

    def count(self) -> int:
        return len(self._points)
