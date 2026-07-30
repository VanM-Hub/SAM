"""
Finalization History.

Ring buffer for finalization event tracking.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class FinalizationHistoryRecord:
    record_id: str = ""; event: str = ""; timestamp: float = 0.0
    state: str = ""; integrity: float = 0.0
    def to_dict(self) -> Dict[str,Any]: return {"record_id":self.record_id,"event":self.event,
        "timestamp":self.timestamp,"state":self.state,"integrity":self.integrity}


class FinalizationHistory:
    def __init__(self, max_size: int = 1000) -> None:
        self._max_size = max_size
        self._buffer: List[Optional[FinalizationHistoryRecord]] = [None]*max_size
        self._head = 0; self._count = 0

    def record(self, rid: str, event: str, state: str, integrity: float = 0.0) -> None:
        r = FinalizationHistoryRecord(record_id=rid, event=event, timestamp=datetime.now().timestamp(),
                                       state=state, integrity=integrity)
        self._buffer[self._head] = r
        self._head = (self._head + 1) % self._max_size
        if self._count < self._max_size: self._count += 1

    @property
    def latest(self) -> Optional[FinalizationHistoryRecord]:
        if self._count == 0: return None
        return self._buffer[(self._head - 1) % self._max_size]

    @property
    def count(self) -> int: return self._count

    def get_all(self) -> List[FinalizationHistoryRecord]:
        if self._count == 0: return []
        if self._count < self._max_size: records = self._buffer[:self._count]
        else: records = self._buffer[self._head:] + self._buffer[:self._head]
        return [r for r in records if r is not None]

    def filter_by_record(self, rid: str) -> List[FinalizationHistoryRecord]:
        return [r for r in self.get_all() if r.record_id == rid]
