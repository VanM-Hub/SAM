"""
Guardian Snapshot Diff Engine.

Compares two runtime snapshots and produces structured diffs.
Synchronous only. No async, no threading, no network.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .state import RuntimeSnapshot, RuntimeState


class SnapshotDiffEngine:
    """
    Synchronous diff engine for runtime snapshots.

    Compares old and new snapshots and produces structured
    diff results (added, removed, changed, unchanged).
    """

    def diff(
        self,
        old_snapshot: RuntimeSnapshot,
        new_snapshot: RuntimeSnapshot,
    ) -> Dict[str, Any]:
        """
        Compute diff between two runtime snapshots.

        Args:
            old_snapshot: The earlier snapshot.
            new_snapshot: The newer snapshot.

        Returns:
            Dict with diff results.
        """
        old_runtimes = {s.runtime_id: s for s in old_snapshot.runtimes.values()}
        new_runtimes = {s.runtime_id: s for s in new_snapshot.runtimes.values()}

        added: List[str] = []
        removed: List[str] = []
        changed: List[Dict[str, Any]] = []
        unchanged_count: int = 0

        old_ids = set(old_runtimes.keys())
        new_ids = set(new_runtimes.keys())

        # Added runtimes
        for rid in sorted(new_ids - old_ids):
            added.append(rid)

        # Removed runtimes
        for rid in sorted(old_ids - new_ids):
            removed.append(rid)

        # Changed and unchanged runtimes
        for rid in sorted(old_ids & new_ids):
            old_state = old_runtimes[rid]
            new_state = new_runtimes[rid]

            changes = self._compute_state_diff(old_state, new_state)
            if changes:
                changed.append({
                    "runtime_id": rid,
                    "changes": changes,
                })
            else:
                unchanged_count += 1

        return {
            "has_changes": len(added) > 0 or len(removed) > 0 or len(changed) > 0,
            "old_snapshot_id": old_snapshot.snapshot_id,
            "new_snapshot_id": new_snapshot.snapshot_id,
            "old_timestamp": old_snapshot.timestamp,
            "new_timestamp": new_snapshot.timestamp,
            "added": added,
            "removed": removed,
            "changed": changed,
            "unchanged": unchanged_count,
            "total_old": old_snapshot.total_runtimes,
            "total_new": new_snapshot.total_runtimes,
        }

    def _compute_state_diff(
        self,
        old: RuntimeState,
        new: RuntimeState,
    ) -> List[Dict[str, Any]]:
        """
        Compute field-level diff between two RuntimeStates.

        Args:
            old: Old runtime state.
            new: New runtime state.

        Returns:
            List of field changes (empty if identical).
        """
        changes: List[Dict[str, Any]] = []

        # Health
        if old.health != new.health:
            changes.append({
                "field": "health",
                "from": old.health.name,
                "to": new.health.name,
            })

        # Status
        if old.status != new.status:
            changes.append({
                "field": "status",
                "from": old.status.name,
                "to": new.status.name,
            })

        # Version
        if str(old.version) != str(new.version):
            changes.append({
                "field": "version",
                "from": str(old.version),
                "to": str(new.version),
            })

        # Trigger count
        if old.statistics.trigger_count != new.statistics.trigger_count:
            changes.append({
                "field": "trigger_count",
                "from": old.statistics.trigger_count,
                "to": new.statistics.trigger_count,
            })

        return changes

    def diff_from_snapshots(
        self,
        snapshots: List[RuntimeSnapshot],
    ) -> List[Dict[str, Any]]:
        """
        Compute sequential diffs across multiple snapshots.

        Args:
            snapshots: List of snapshots in chronological order.

        Returns:
            List of diff results between consecutive snapshots.
        """
        diffs: List[Dict[str, Any]] = []
        for i in range(1, len(snapshots)):
            diff_result = self.diff(snapshots[i - 1], snapshots[i])
            diffs.append(diff_result)
        return diffs
