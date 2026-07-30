"""
Lifecycle Engine.

Manages state transitions for ApprovalSession lifecycle.
Deterministic. Does NOT execute approval.
"""

import uuid
from datetime import datetime
from typing import Optional
from .approval_lifecycle import ApprovalLifecycle, ApprovalLifecycleState, LifecycleTransition, LifecycleStatistics, LifecycleSnapshot, LifecycleMetadata
from .lifecycle_rules import LifecycleRules
from .lifecycle_history import LifecycleHistory


class LifecycleEngine:
    def __init__(self) -> None:
        self._lifecycles: list = []
        self._history = LifecycleHistory()

    def initialize(self, session_id: str, session_ready: bool = False) -> ApprovalLifecycle:
        lifecycle = ApprovalLifecycle(
            lifecycle_id=str(uuid.uuid4()),
            session_id=session_id,
            timestamp=datetime.now().timestamp(),
            state=ApprovalLifecycleState.CREATED,
            transitions=[],
            session_ready=session_ready,
        )
        self._lifecycles.append(lifecycle)
        self._history.record(lifecycle.lifecycle_id, "created", "NONE", "CREATED")
        return lifecycle

    def transition(self, lifecycle_id: str, target: ApprovalLifecycleState, reason: str = "") -> Optional[ApprovalLifecycle]:
        idx = self._find_index(lifecycle_id)
        if idx is None: return None

        current = self._lifecycles[idx]
        if not LifecycleRules.can_transition(current.state, target): return None

        transition = LifecycleTransition(
            from_state=current.state.name, to_state=target.name,
            timestamp=datetime.now().timestamp(), reason=reason or f"{current.state.name}→{target.name}"
        )
        new_lifecycle = ApprovalLifecycle(
            lifecycle_id=current.lifecycle_id, session_id=current.session_id,
            timestamp=datetime.now().timestamp(), state=target,
            transitions=list(current.transitions) + [transition],
            session_ready=current.session_ready,
        )
        self._lifecycles[idx] = new_lifecycle
        self._history.record(lifecycle_id, "transition", current.state.name, target.name)
        return new_lifecycle

    def close(self, lifecycle_id: str, reason: str = "completed") -> Optional[ApprovalLifecycle]:
        return self.transition(lifecycle_id, ApprovalLifecycleState.CLOSED, reason)

    def cancel(self, lifecycle_id: str, reason: str = "cancelled") -> Optional[ApprovalLifecycle]:
        c = self._find(lifecycle_id)
        if not c: return None
        if not LifecycleRules.is_cancellable(c.state): return None
        return self.transition(lifecycle_id, ApprovalLifecycleState.CANCELLED, reason)

    def latest(self) -> Optional[ApprovalLifecycle]:
        return self._lifecycles[-1] if self._lifecycles else None

    @property
    def count(self) -> int: return len(self._lifecycles)

    @property
    def history(self) -> LifecycleHistory: return self._history

    def get_statistics(self) -> LifecycleStatistics:
        counts = {"created":0,"validated":0,"ready":0,"waiting":0,"cancelled":0,"closed":0}
        for lc in self._lifecycles:
            n = lc.state.name.lower()
            if n in counts: counts[n] += 1
        return LifecycleStatistics(total=self.count, **counts)

    def create_snapshot(self) -> LifecycleSnapshot:
        return LifecycleSnapshot(
            snapshot_id=str(uuid.uuid4()), timestamp=datetime.now().timestamp(),
            lifecycles=list(self._lifecycles[-20:]),
            statistics=self.get_statistics()
        )

    def _find_index(self, lifecycle_id: str) -> Optional[int]:
        for i, lc in enumerate(self._lifecycles):
            if lc.lifecycle_id == lifecycle_id: return i
        return None

    def _find(self, lifecycle_id: str) -> Optional[ApprovalLifecycle]:
        i = self._find_index(lifecycle_id)
        return self._lifecycles[i] if i is not None else None
