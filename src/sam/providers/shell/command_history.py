"""Shell Command History — riwayat preview command (read-only).

Sprint 146 — Shell Provider.
Mencatat riwayat preview command. Tidak ada eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ShellHistoryEntry:
    """Satu entri riwayat preview shell (immutable)."""
    command_id: str
    command_text: str
    validated: bool = True
    executed: bool = False
    external_calls: int = 0


class ShellHistory:
    """Riwayat preview command. Append + read-only query."""

    def __init__(self) -> None:
        self._entries: List[ShellHistoryEntry] = []

    def record(self, entry: ShellHistoryEntry) -> None:
        self._entries.append(entry)

    def entries(self) -> List[ShellHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def total_external_calls(self) -> int:
        return sum(e.external_calls for e in self._entries)


__all__ = ["ShellHistory", "ShellHistoryEntry"]
