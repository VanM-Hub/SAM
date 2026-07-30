"""
Session History.

Ring buffer for session lifecycle tracking.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SessionHistoryRecord:
    session_id: str = ""; event: str = ""; timestamp: float = 0.0
    previous_state: str = ""; new_state: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"session_id":self.session_id,"event":self.event,
        "timestamp":self.timestamp,"from":self.previous_state,"to":self.new_state}


class SessionHistory:
    def __init__(self, max_size: int = 1000) -> None:
        self._max_size = max_size
        self._buffer: List[Optional[SessionHistoryRecord]] = [None]*max_size
        self._head = 0; self._count = 0

    def record(self, session_id: str, event: str, prev: str, new_s: str) -> None:
        r = SessionHistoryRecord(session_id=session_id, event=event, timestamp=datetime.now().timestamp(),
                                  previous_state=prev, new_state=new_s)
        self._buffer[self._head] = r
        self._head = (self._head + 1) % self._max_size
        if self._count < self._max_size: self._count += 1

    @property
    def latest(self) -> Optional[SessionHistoryRecord]:
        if self._count == 0: return None
        return self._buffer[(self._head - 1) % self._max_size]

    @property
    def count(self) -> int: return self._count

    def get_all(self) -> List[SessionHistoryRecord]:
        if self._count == 0: return []
        if self._count < self._max_size: records = self._buffer[:self._count]
        else: records = self._buffer[self._head:] + self._buffer[:self._head]
        return [r for r in records if r is not None]

    def filter_by_session(self, session_id: str) -> List[SessionHistoryRecord]:
        return [r for r in self.get_all() if r.session_id == session_id]
