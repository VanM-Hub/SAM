"""State History — histori state."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.runtime_state import StateHistoryEntry


class StateHistory:
    """Histori state — preview-only."""

    def __init__(self) -> None:
        self._entries: List[StateHistoryEntry] = []

    def record(self, entry_id: str, state: str, transition: str = "",
               timestamp: float = 0.0) -> StateHistoryEntry:
        e = StateHistoryEntry(
            entry_id=entry_id,
            state=state,
            transition=transition,
            timestamp=timestamp,
        )
        self._entries.append(e)
        return e

    def get_all(self) -> List[StateHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def last_state(self) -> str:
        if self._entries:
            return self._entries[-1].state
        return ""

    def filter_by_state(self, state: str) -> List[StateHistoryEntry]:
        return [e for e in self._entries if e.state == state]
