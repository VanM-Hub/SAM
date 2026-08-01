"""Sprint 272 - Presentation Layer Foundation: dashboard bridge (read-only).

Bridge ke lapisan dashboard TIDAK diubah; hanya membaca snapshot metadata
secara statis tanpa memanggil subsystem lain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class DashboardBridgeSnapshot:
    """Snapshot metadata dashboard yang dibaca bridge (read-only)."""

    dashboard_id: str = "unknown"
    mode: str = "dashboard"
    runtime_scope: Tuple[str, ...] = ("dashboard",)

    def as_dict(self) -> dict:
        return {
            "dashboard_id": self.dashboard_id,
            "mode": self.mode,
            "runtime_scope": list(self.runtime_scope),
        }


@dataclass(frozen=True)
class DashboardBridge:
    """Bridge read-only untuk dashboard desktop (tanpa IO/thread)."""

    snapshot: DashboardBridgeSnapshot = field(
        default_factory=DashboardBridgeSnapshot
    )

    def read_only(self) -> bool:
        return True

    def scope(self) -> Tuple[str, ...]:
        return self.snapshot.runtime_scope

    def as_dict(self) -> dict:
        return {
            "read_only": True,
            "snapshot": self.snapshot.as_dict(),
        }
