"""State Snapshot — snapshot state."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_state import StateSnapshot


class SnapshotEngine:
    """Engine snapshot — preview-only."""

    def __init__(self) -> None:
        self._snapshots: Dict[str, StateSnapshot] = {}

    def create(self, snapshot_id: str, timestamp: float, state: str,
               components: Dict[str, str] = None) -> StateSnapshot:
        s = StateSnapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            state=state,
            components=components or {},
        )
        self._snapshots[snapshot_id] = s
        return s

    def get(self, snapshot_id: str) -> StateSnapshot | None:
        return self._snapshots.get(snapshot_id)

    def count(self) -> int:
        return len(self._snapshots)

    def list_all(self) -> List[StateSnapshot]:
        return list(self._snapshots.values())
