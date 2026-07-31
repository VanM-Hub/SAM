"""ArtifactHistory — riwayat artifact in-memory (tanpa disk)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ArtifactHistoryEntry:
    name: str = ""
    action: str = "record"


@dataclass(frozen=True)
class ArtifactHistory:
    """Riwayat artifact in-memory. Tidak menulis ke disk."""
    _entries: Tuple[ArtifactHistoryEntry, ...] = ()

    def record(self, entry: ArtifactHistoryEntry) -> "ArtifactHistory":
        return ArtifactHistory(self._entries + (entry,))

    def all(self) -> Tuple[ArtifactHistoryEntry, ...]:
        return self._entries

    def count(self) -> int:
        return len(self._entries)


class ArtifactRecorder:
    """Perekam riwayat artifact (in-memory, no disk write)."""

    def __init__(self) -> None:
        self._history = ArtifactHistory()

    def append(self, name: str) -> ArtifactHistory:
        self._history = self._history.record(ArtifactHistoryEntry(name=name))
        return self._history
