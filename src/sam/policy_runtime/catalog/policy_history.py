"""Policy History — riwayat policy read-only (Sprint 208)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class PolicyHistoryEntry:
    """Entri riwayat (immutable)."""
    policy_id: str = ""
    action: str = "created"
    timestamp: str = ""


class PolicyHistory:
    """Riwayat policy in-memory. Append hanya komposisi (no write)."""

    def __init__(self) -> None:
        self._entries: List[PolicyHistoryEntry] = []

    def record(self, entry: PolicyHistoryEntry) -> None:
        self._entries.append(entry)

    def all_entries(self) -> List[PolicyHistoryEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def by_policy(self, policy_id: str) -> List[PolicyHistoryEntry]:
        return [
            e for e in self._entries if e.policy_id == policy_id
        ]
