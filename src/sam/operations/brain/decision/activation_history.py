"""
Activation History.

Ring buffer for activation event tracking.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class ActivationHistoryRecord:
    activation_id: str = ""; event: str = ""; timestamp: float = 0.0
    state: str = ""; decision: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"activation_id":self.activation_id,"event":self.event,
        "timestamp":self.timestamp,"state":self.state,"decision":self.decision}


class ActivationHistory:
    def __init__(self, max_size: int = 1000) -> None:
        self._max_size = max_size
        self._buffer: List[Optional[ActivationHistoryRecord]] = [None]*max_size
        self._head = 0; self._count = 0

    def record(self, activation_id: str, event: str, state: str, decision: str) -> None:
        r = ActivationHistoryRecord(activation_id=activation_id, event=event, timestamp=datetime.now().timestamp(),
                                     state=state, decision=decision)
        self._buffer[self._head] = r
        self._head = (self._head + 1) % self._max_size
        if self._count < self._max_size: self._count += 1

    @property
    def latest(self) -> Optional[ActivationHistoryRecord]:
        if self._count == 0: return None
        return self._buffer[(self._head - 1) % self._max_size]

    @property
    def count(self) -> int: return self._count

    def get_all(self) -> List[ActivationHistoryRecord]:
        if self._count == 0: return []
        if self._count < self._max_size: records = self._buffer[:self._count]
        else: records = self._buffer[self._head:] + self._buffer[:self._head]
        return [r for r in records if r is not None]

    def filter_by_activation(self, activation_id: str) -> List[ActivationHistoryRecord]:
        return [r for r in self.get_all() if r.activation_id == activation_id]
