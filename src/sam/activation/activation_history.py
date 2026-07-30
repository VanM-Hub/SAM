"""Activation History — riwayat aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_package import ActivationPackage


@dataclass(frozen=True)
class HistoryEntry:
    entry_id: str = ""
    package_id: str = ""
    action: str = ""
    timestamp: float = 0.0
    status: str = ""


class ActivationHistory:
    """Riwayat aktivasi — immutable entry."""

    def __init__(self):
        self._entries: List[HistoryEntry] = []

    def record(self, package: ActivationPackage, action: str,
               timestamp: float = 0.0) -> HistoryEntry:
        entry = HistoryEntry(
            entry_id=f"hist_{len(self._entries) + 1}",
            package_id=package.package_id,
            action=action,
            timestamp=timestamp,
            status=package.status,
        )
        self._entries.append(entry)
        return entry

    def list(self, limit: int = 20) -> List[HistoryEntry]:
        return self._entries[-limit:]

    def count(self) -> int:
        return len(self._entries)

    def by_package(self, pid: str) -> List[HistoryEntry]:
        return [e for e in self._entries if e.package_id == pid]

    def clear(self) -> None:
        self._entries.clear()
