"""
Guardian Snapshot Manager.

Manages point-in-time snapshots of runtime state.
Supports current, history, diff, and rollback preview.

Synchronous only. No async, no threading, no network.
Rollback preview produces DTOs only — does NOT change state.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from .state import RuntimeSnapshot, RuntimeState


class GuardianSnapshotManager:
    """
    Synchronous snapshot manager for Guardian runtime state.

    Maintains a ring buffer of snapshots and provides
    diff and rollback preview capabilities.
    """

    def __init__(self, max_history: int = 100) -> None:
        self._max_history = max_history
        self._history: List[RuntimeSnapshot] = []

    def capture(self, snapshot: RuntimeSnapshot) -> None:
        """
        Capture a new snapshot.

        Args:
            snapshot: The snapshot to record.
        """
        self._history.append(snapshot)
        if len(self._history) > self._max_history:
            self._history.pop(0)

    @property
    def current(self) -> Optional[RuntimeSnapshot]:
        """Get the most recent snapshot."""
        if not self._history:
            return None
        return self._history[-1]

    @property
    def history(self) -> List[RuntimeSnapshot]:
        """Get all captured snapshots (oldest first)."""
        return list(self._history)

    @property
    def count(self) -> int:
        """Get the number of captured snapshots."""
        return len(self._history)

    @property
    def max_size(self) -> int:
        """Get the maximum number of snapshots."""
        return self._max_history

    def get(self, index: int) -> Optional[RuntimeSnapshot]:
        """
        Get a snapshot by index (0 = oldest).

        Args:
            index: Zero-based index from oldest.

        Returns:
            RuntimeSnapshot or None if out of range.
        """
        if 0 <= index < len(self._history):
            return self._history[index]
        return None

    def get_by_id(self, snapshot_id: str) -> Optional[RuntimeSnapshot]:
        """
        Get a snapshot by its ID.

        Args:
            snapshot_id: The snapshot ID to find.

        Returns:
            RuntimeSnapshot or None if not found.
        """
        for snap in reversed(self._history):
            if snap.snapshot_id == snapshot_id:
                return snap
        return None

    def diff(
        self,
        snapshot_a: Optional[RuntimeSnapshot] = None,
        snapshot_b: Optional[RuntimeSnapshot] = None,
    ) -> Dict[str, Any]:
        """
        Compute diff between two snapshots.

        Args:
            snapshot_a: Earlier snapshot (default: oldest).
            snapshot_b: Later snapshot (default: current).

        Returns:
            Dict with diff results.
        """
        a = snapshot_a or (self._history[0] if len(self._history) > 0 else None)
        b = snapshot_b or self.current

        if a is None or b is None:
            return {
                "has_diff": False,
                "error": "Need at least two snapshots to diff",
            }

        added: List[str] = []
        removed: List[str] = []
        changed: List[Dict[str, Any]] = []
        unchanged: int = 0

        a_runtimes = {s.runtime_id: s for s in a.runtimes.values()}
        b_runtimes = {s.runtime_id: s for s in b.runtimes.values()}

        for rid, state_b in b_runtimes.items():
            if rid not in a_runtimes:
                added.append(rid)
            else:
                state_a = a_runtimes[rid]
                if (
                    state_a.status != state_b.status
                    or state_a.health != state_b.health
                    or str(state_a.version) != str(state_b.version)
                ):
                    changed.append({
                        "runtime_id": rid,
                        "from_status": state_a.status.name,
                        "to_status": state_b.status.name,
                        "from_health": state_a.health.name,
                        "to_health": state_b.health.name,
                        "from_version": str(state_a.version),
                        "to_version": str(state_b.version),
                    })
                else:
                    unchanged += 1

        for rid in a_runtimes:
            if rid not in b_runtimes:
                removed.append(rid)

        return {
            "has_diff": len(added) > 0 or len(removed) > 0 or len(changed) > 0,
            "snapshot_a_id": a.snapshot_id,
            "snapshot_b_id": b.snapshot_id,
            "a_timestamp": a.timestamp,
            "b_timestamp": b.timestamp,
            "added": added,
            "removed": removed,
            "changed": changed,
            "unchanged": unchanged,
        }

    def rollback_preview(
        self,
        target_snapshot_id: Optional[str] = None,
        target_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a rollback preview DTO.

        PREVIEW ONLY — does NOT change any state.

        Args:
            target_snapshot_id: Rollback to this snapshot ID.
            target_index: Rollback to this index (alternative to ID).

        Returns:
            Dict with rollback preview DTO.
        """
        target = None
        if target_snapshot_id:
            target = self.get_by_id(target_snapshot_id)
        elif target_index is not None:
            target = self.get(target_index)

        if target is None:
            return {
                "can_rollback": False,
                "error": "Target snapshot not found",
            }

        current = self.current
        if current is None:
            return {
                "can_rollback": False,
                "error": "No current snapshot to rollback from",
            }

        diff_result = self.diff(target, current)

        return {
            "can_rollback": True,
            "rollback_preview_id": str(uuid.uuid4()),
            "target_snapshot_id": target.snapshot_id,
            "target_timestamp": target.timestamp,
            "current_snapshot_id": current.snapshot_id,
            "current_timestamp": current.timestamp,
            "runtimes_in_target": target.total_runtimes,
            "runtimes_in_current": current.total_runtimes,
            "diff": diff_result,
            "warning": "PREVIEW ONLY — does not change any state",
            "timestamp": datetime.now().timestamp(),
        }

    def clear(self) -> None:
        """Clear all snapshots."""
        self._history.clear()
