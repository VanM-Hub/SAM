"""LifecycleHistory (Sprint 264).

Program D - Runtime Services & Deployment.
Riwayat transisi lifecycle (append-only, deterministic).
"""
from __future__ import annotations
from typing import List

from .transition import LifecycleTransition


class LifecycleHistory:
    """Riwayat lifecycle (append-only)."""

    def __init__(self) -> None:
        self._entries: List[LifecycleTransition] = []

    def append(self, transition: LifecycleTransition) -> None:
        self._entries.append(transition)

    def entries(self) -> List[LifecycleTransition]:
        return list(self._entries)

    def states(self) -> List[str]:
        result = []
        for t in self._entries:
            if not result or result[-1] != t.source.name:
                result.append(t.source.name)
            result.append(t.target.name)
        # dedup berurutan
        deduped = []
        for s in result:
            if not deduped or deduped[-1] != s:
                deduped.append(s)
        return deduped

    def count(self) -> int:
        return len(self._entries)

    def last(self) -> str:
        if not self._entries:
            return "created"
        return self._entries[-1].target.name
