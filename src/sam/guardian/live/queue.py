"""
Guardian Decision Queue.

Immutable queue for decision inputs. Preview only. Does NOT execute.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict
import uuid

from .decision_input import DecisionInput, DecisionStatistics, DecisionSnapshot


class DecisionQueue:
    """Immutable queue for DecisionInput items."""

    def __init__(self, max_size: int = 500) -> None:
        self._max_size = max_size
        self._items: List[DecisionInput] = []

    def enqueue(self, item: DecisionInput) -> None:
        self._items.append(item)
        if len(self._items) > self._max_size:
            self._items.pop(0)

    @property
    def count(self) -> int:
        return len(self._items)

    def peek(self, index: int = -1) -> Optional[DecisionInput]:
        if not self._items:
            return None
        return self._items[index]

    def history(self, limit: int = 50) -> List[DecisionInput]:
        return self._items[-limit:] if limit > 0 else list(self._items)

    @property
    def eligible_count(self) -> int:
        from .decision_input import EligibilityStatus
        return sum(1 for i in self._items if i.eligibility == EligibilityStatus.ELIGIBLE)

    @property
    def blocked_count(self) -> int:
        from .decision_input import EligibilityStatus
        return sum(1 for i in self._items if i.eligibility == EligibilityStatus.BLOCKED)

    def get_statistics(self) -> DecisionStatistics:
        by_priority: Dict[str, int] = defaultdict(int)
        total_conf = 0
        for item in self._items:
            name = f"P{item.priority_score}"
            by_priority[name] += 1
            total_conf += item.confidence
        avg_conf = round(total_conf / len(self._items), 2) if self._items else 0.0
        return DecisionStatistics(
            total=len(self._items),
            eligible=self.eligible_count,
            blocked=self.blocked_count,
            by_priority=dict(by_priority),
            average_confidence=avg_conf,
            timestamp=datetime.now().timestamp(),
        )

    def create_snapshot(self) -> DecisionSnapshot:
        stats = self.get_statistics()
        return DecisionSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            total_queue=self.count,
            decisions=list(self._items[-20:]) if self._items else [],
            statistics=stats,
        )

    def clear(self) -> None:
        self._items.clear()
