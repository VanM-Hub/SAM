"""Runtime Registry — registry runtime (Sprint 160).

Agent Runtime — mendaftarkan runtime yang dikenal agent. Read-only query.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .runtime_request import RuntimeRequest


@dataclass(frozen=True)
class RuntimeEntry:
    """Entri runtime terdaftar (immutable)."""
    name: str
    preview_only: bool = True
    available: bool = True


class RuntimeRegistry:
    """Registry runtime. Append + read-only query."""

    def __init__(self) -> None:
        self._entries: Dict[str, RuntimeEntry] = {}

    def register(self, entry: RuntimeEntry) -> bool:
        if entry.name in self._entries:
            return False
        self._entries[entry.name] = entry
        return True

    def register_many(self, names: List[str]) -> None:
        for n in names:
            self.register(RuntimeEntry(name=n))

    def get(self, name: str) -> Optional[RuntimeEntry]:
        return self._entries.get(name)

    def names(self) -> List[str]:
        return list(self._entries.keys())

    def count(self) -> int:
        return len(self._entries)

    def has(self, name: str) -> bool:
        return name in self._entries

    def supports(self, request: RuntimeRequest) -> bool:
        entry = self._entries.get(request.runtime_name)
        return entry is not None and entry.available


__all__ = ["RuntimeRegistry", "RuntimeEntry", "RuntimeRequest"]
