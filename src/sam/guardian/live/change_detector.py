"""
Guardian Change Detector.

Detects changes between runtime snapshots and classifies them.
All rule-based. No AI, no machine learning.
Synchronous only.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from .transition import RuntimeTransition, TransitionType, ImpactLevel
from .state import RuntimeSnapshot, RuntimeState
from .diff_engine import SnapshotDiffEngine


class ChangeDetector:
    """
    Rule-based change detector for runtime transitions.

    Detects:
        - Runtime added
        - Runtime removed
        - Health changed
        - Version changed
        - State changed
        - Registry changed

    Assigns severity and priority based on rules.
    """

    def __init__(self) -> None:
        self._diff_engine = SnapshotDiffEngine()

    def detect(
        self,
        old_snapshot: RuntimeSnapshot,
        new_snapshot: RuntimeSnapshot,
    ) -> List[RuntimeTransition]:
        """
        Detect all changes between two snapshots.

        Args:
            old_snapshot: The earlier snapshot.
            new_snapshot: The newer snapshot.

        Returns:
            List of RuntimeTransition for each detected change.
        """
        transitions: List[RuntimeTransition] = []
        now = datetime.now().timestamp()

        diff_result = self._diff_engine.diff(old_snapshot, new_snapshot)

        old_runtimes = {s.runtime_id: s for s in old_snapshot.runtimes.values()}
        new_runtimes = {s.runtime_id: s for s in new_snapshot.runtimes.values()}

        # 1. Added runtimes
        for rid in diff_result["added"]:
            new_state = new_runtimes.get(rid)
            transitions.append(RuntimeTransition(
                transition_id=str(uuid.uuid4()),
                transition_type=TransitionType.RUNTIME_ADDED,
                runtime_id=rid,
                timestamp=now,
                current_state=new_state.to_dict() if new_state else None,
                impact=ImpactLevel.LOW,
                details={"action": "added"},
            ))

        # 2. Removed runtimes
        for rid in diff_result["removed"]:
            old_state = old_runtimes.get(rid)
            transitions.append(RuntimeTransition(
                transition_id=str(uuid.uuid4()),
                transition_type=TransitionType.RUNTIME_REMOVED,
                runtime_id=rid,
                timestamp=now,
                previous_state=old_state.to_dict() if old_state else None,
                impact=ImpactLevel.MEDIUM,
                details={"action": "removed"},
            ))

        # 3. Changed runtimes
        for change in diff_result["changed"]:
            rid = change["runtime_id"]
            old_state = old_runtimes.get(rid)
            new_state = new_runtimes.get(rid)
            field_changes = change["changes"]

            for field_change in field_changes:
                trans_type, impact = self._classify_change(field_change)
                transitions.append(RuntimeTransition(
                    transition_id=str(uuid.uuid4()),
                    transition_type=trans_type,
                    runtime_id=rid,
                    timestamp=now,
                    previous_state=old_state.to_dict() if old_state else None,
                    current_state=new_state.to_dict() if new_state else None,
                    impact=impact,
                    details={"field_change": field_change},
                ))

        return transitions

    def _classify_change(
        self,
        field_change: Dict[str, Any],
    ) -> tuple:
        """
        Classify a field change into transition type and impact.

        All rule-based.

        Args:
            field_change: Dict with 'field', 'from', 'to' keys.

        Returns:
            Tuple of (TransitionType, ImpactLevel).
        """
        field = field_change.get("field", "")

        if field == "health":
            to_val = field_change.get("to", "")
            if to_val == "CRITICAL":
                return TransitionType.HEALTH_CHANGED, ImpactLevel.CRITICAL
            elif to_val == "DEGRADED":
                return TransitionType.HEALTH_CHANGED, ImpactLevel.HIGH
            else:
                return TransitionType.HEALTH_CHANGED, ImpactLevel.MEDIUM

        elif field == "status":
            from_val = field_change.get("from", "")
            to_val = field_change.get("to", "")
            if to_val in ("ERROR", "STOPPED"):
                return TransitionType.STATUS_CHANGED, ImpactLevel.HIGH
            elif from_val in ("ERROR", "STOPPED") and to_val == "RUNNING":
                return TransitionType.STATUS_CHANGED, ImpactLevel.MEDIUM
            else:
                return TransitionType.STATUS_CHANGED, ImpactLevel.LOW

        elif field == "version":
            return TransitionType.VERSION_CHANGED, ImpactLevel.MEDIUM

        elif field == "trigger_count":
            return TransitionType.STATUS_CHANGED, ImpactLevel.LOW

        return TransitionType.STATUS_CHANGED, ImpactLevel.LOW

    def detect_registry_change(
        self,
        old_registry_count: int,
        new_registry_count: int,
    ) -> Optional[RuntimeTransition]:
        """
        Detect a registry-level change.

        Args:
            old_registry_count: Previous registry count.
            new_registry_count: New registry count.

        Returns:
            RuntimeTransition if count changed, else None.
        """
        if old_registry_count == new_registry_count:
            return None

        return RuntimeTransition(
            transition_id=str(uuid.uuid4()),
            transition_type=TransitionType.REGISTRY_CHANGED,
            runtime_id="__registry__",
            timestamp=datetime.now().timestamp(),
            previous_state={"count": old_registry_count},
            current_state={"count": new_registry_count},
            impact=ImpactLevel.MEDIUM,
            details={
                "old_count": old_registry_count,
                "new_count": new_registry_count,
            },
        )
