"""
Guardian Live Dashboard Sync Bridge.

Provides 6 immutable dashboard cards for runtime synchronization.
All DTOs are frozen. No async, no threading, no network.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime

from .state import RuntimeVersion

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


@dataclass(frozen=True)
class RuntimeRegistryCard:
    """Runtime registry overview card."""
    total_runtimes: int
    versions: Dict[str, int]
    statuses: Dict[str, int]
    healths: Dict[str, int]
    runtime_ids: List[str]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Runtime Registry",
            "total_runtimes": self.total_runtimes,
            "versions": dict(self.versions),
            "statuses": dict(self.statuses),
            "healths": dict(self.healths),
            "runtime_ids": list(self.runtime_ids),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class SynchronizationCard:
    """Synchronization status card."""
    sync_count: int
    has_last_sync: bool
    runtime_count: int
    last_sync_summary: Optional[Dict[str, Any]]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Synchronization",
            "sync_count": self.sync_count,
            "has_last_sync": self.has_last_sync,
            "runtime_count": self.runtime_count,
            "last_sync_summary": self.last_sync_summary,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class VersionMatrixCard:
    """Version distribution matrix card."""
    current_version: str
    version_counts: Dict[str, int]
    all_matching: bool
    mismatches: List[str]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Version Matrix",
            "current_version": self.current_version,
            "version_counts": dict(self.version_counts),
            "all_matching": self.all_matching,
            "mismatches": list(self.mismatches),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class SnapshotCard:
    """Snapshot overview card."""
    total_snapshots: int
    current_snapshot_id: Optional[str]
    current_timestamp: Optional[float]
    total_runtimes_in_current: Optional[int]
    max_size: int
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Snapshot",
            "total_snapshots": self.total_snapshots,
            "current_snapshot_id": self.current_snapshot_id,
            "current_timestamp": self.current_timestamp,
            "total_runtimes_in_current": self.total_runtimes_in_current,
            "max_size": self.max_size,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class ConsistencyCard:
    """Consistency validation results card."""
    is_consistent: bool
    check_results: Dict[str, bool]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Consistency",
            "is_consistent": self.is_consistent,
            "check_results": dict(self.check_results),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class SyncHealthCard:
    """Synchronization health overview card."""
    registry_count: int
    snapshot_count: int
    sync_count: int
    is_consistent: bool
    total_errors: int
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card": "Sync Health",
            "registry_count": self.registry_count,
            "snapshot_count": self.snapshot_count,
            "sync_count": self.sync_count,
            "is_consistent": self.is_consistent,
            "total_errors": self.total_errors,
            "timestamp": self.timestamp,
        }


class LiveDashboardSyncBridge:
    """
    Bridge for synchronization dashboard cards.

    Provides 6 immutable cards:
        1. Runtime Registry
        2. Synchronization
        3. Version Matrix
        4. Snapshot
        5. Consistency
        6. Sync Health
    """

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    def get_runtime_registry_card(self) -> RuntimeRegistryCard:
        """Get Runtime Registry card."""
        stats = self._runtime.registry.statistics()
        return RuntimeRegistryCard(
            total_runtimes=stats["total_runtimes"],
            versions=stats.get("versions", {}),
            statuses=stats.get("statuses", {}),
            healths=stats.get("healths", {}),
            runtime_ids=list(self._runtime.registry.ids),
            timestamp=datetime.now().timestamp(),
        )

    def get_synchronization_card(self) -> SynchronizationCard:
        """Get Synchronization status card."""
        summary = self._runtime.synchronizer.last_summary
        return SynchronizationCard(
            sync_count=self._runtime.synchronizer.sync_count,
            has_last_sync=summary is not None,
            runtime_count=(
                summary["runtime_count"]
                if summary else 0
            ),
            last_sync_summary=summary,
            timestamp=datetime.now().timestamp(),
        )

    def get_version_matrix_card(self) -> VersionMatrixCard:
        """Get Version Matrix card."""
        runtimes = self._runtime.registry.list()
        versions: Dict[str, int] = {}
        mismatches: List[str] = []
        current = str(RuntimeVersion.current())

        for s in runtimes:
            v = str(s.version)
            versions[v] = versions.get(v, 0) + 1
            if v != current:
                mismatches.append(s.runtime_id)

        return VersionMatrixCard(
            current_version=current,
            version_counts=versions,
            all_matching=len(mismatches) == 0,
            mismatches=mismatches,
            timestamp=datetime.now().timestamp(),
        )

    def get_snapshot_card(self) -> SnapshotCard:
        """Get Snapshot card."""
        current = self._runtime.snapshot_manager.current
        return SnapshotCard(
            total_snapshots=self._runtime.snapshot_manager.count,
            current_snapshot_id=current.snapshot_id if current else None,
            current_timestamp=current.timestamp if current else None,
            total_runtimes_in_current=current.total_runtimes if current else None,
            max_size=self._runtime.snapshot_manager.max_size,
            timestamp=datetime.now().timestamp(),
        )

    def get_consistency_card(self) -> ConsistencyCard:
        """Get Consistency validation card."""
        results = self._runtime.validator.validate_all()
        check_results = {
            k: v["pass"] for k, v in results.items()
            if isinstance(v, dict) and "pass" in v
        }
        return ConsistencyCard(
            is_consistent=results.get("overall_consistent", False),
            check_results=check_results,
            timestamp=datetime.now().timestamp(),
        )

    def get_sync_health_card(self) -> SyncHealthCard:
        """Get Sync Health card."""
        return SyncHealthCard(
            registry_count=self._runtime.registry.count,
            snapshot_count=self._runtime.snapshot_manager.count,
            sync_count=self._runtime.synchronizer.sync_count,
            is_consistent=self._runtime.validator.is_consistent(),
            total_errors=0,
            timestamp=datetime.now().timestamp(),
        )

    @property
    def card_count(self) -> int:
        """Get the number of dashboard cards."""
        return 6

    def get_all_cards(self) -> Dict[str, Any]:
        """Get all 6 dashboard sync cards."""
        return {
            "runtime_registry": self.get_runtime_registry_card().to_dict(),
            "synchronization": self.get_synchronization_card().to_dict(),
            "version_matrix": self.get_version_matrix_card().to_dict(),
            "snapshot": self.get_snapshot_card().to_dict(),
            "consistency": self.get_consistency_card().to_dict(),
            "sync_health": self.get_sync_health_card().to_dict(),
        }
