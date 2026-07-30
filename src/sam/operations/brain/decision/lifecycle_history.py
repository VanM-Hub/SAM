"""
Lifecycle History.

Ring buffer for lifecycle event tracking.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class LifecycleHistoryRecord:
    lifecycle_id: str = ""; event: str = ""; timestamp: float = 0.0
    from_state: str = ""; to_state: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"lifecycle_id":self.lifecycle_id,"event":self.event,
        "timestamp":self.timestamp,"from":self.from_state,"to":self.to_state}


class LifecycleHistory:
    def __init__(self, max_size: int = 1000) -> None:
        self._max_size = max_size
        self._buffer: List[Optional[LifecycleHistoryRecord]] = [None]*max_size
        self._head = 0; self._count = 0

    def record(self, lifecycle_id: str, event: str, from_s: str, to_s: str) -> None:
        r = LifecycleHistoryRecord(lifecycle_id=lifecycle_id, event=event, timestamp=datetime.now().timestamp(),
                                    from_state=from_s, to_state=to_s)
        self._buffer[self._head] = r
        self._head = (self._head + 1) % self._max_size
        if self._count < self._max_size: self._count += 1

    @property
    def latest(self) -> Optional[LifecycleHistoryRecord]:
        if self._count == 0: return None
        return self._buffer[(self._head - 1) % self._max_size]

    @property
    def count(self) -> int: return self._count

    def get_all(self) -> List[LifecycleHistoryRecord]:
        if self._count == 0: return []
        if self._count < self._max_size: records = self._buffer[:self._count]
        else: records = self._buffer[self._head:] + self._buffer[:self._head]
        return [r for r in records if r is not None]

    def filter_by_lifecycle(self, lifecycle_id: str) -> List[LifecycleHistoryRecord]:
        return [r for r in self.get_all() if r.lifecycle_id == lifecycle_id]
