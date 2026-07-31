"""Runtime Queue — antrian runtime (Sprint 160).

Agent Runtime — antrian menentukan urutan runtime yang akan diproses.
Deterministik, tidak mengeksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class RuntimeQueueEntry:
    """Satu entri antrian runtime (immutable)."""
    runtime_name: str
    position: int
    processed: bool = False
    external_calls: int = 0


class RuntimeQueue:
    """Antrian runtime. Append + read-only query. Deterministik."""

    def __init__(self) -> None:
        self._entries: List[RuntimeQueueEntry] = []

    def enqueue(self, runtime_name: str) -> RuntimeQueueEntry:
        entry = RuntimeQueueEntry(
            runtime_name=runtime_name, position=len(self._entries)
        )
        self._entries.append(entry)
        return entry

    def enqueue_many(self, runtimes: List[str]) -> None:
        for r in runtimes:
            self.enqueue(r)

    def entries(self) -> List[RuntimeQueueEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def pending(self) -> List[RuntimeQueueEntry]:
        return [e for e in self._entries if not e.processed]

    def next_pending(self) -> Optional[RuntimeQueueEntry]:
        pending = self.pending()
        if not pending:
            return None
        # urutkan sesuai posisi
        return min(pending, key=lambda e: e.position)

    def mark_processed(self, runtime_name: str) -> bool:
        for i, e in enumerate(self._entries):
            if e.runtime_name == runtime_name and not e.processed:
                from dataclasses import replace
                self._entries[i] = replace(e, processed=True)
                return True
        return False
