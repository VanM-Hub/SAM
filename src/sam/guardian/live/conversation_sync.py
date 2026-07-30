"""
Guardian Live Conversation Sync Bridge.

Provides 10 DTO-only query methods for runtime synchronization.
All methods return frozen dicts. No async, no threading, no network.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime

from .state import RuntimeState, RuntimeVersion

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveConversationSyncBridge:
    """
    Bridge for runtime synchronization queries.

    Provides 10 query methods:
        1. runtime_state     - Get current runtime state
        2. registry          - List all registered runtimes
        3. snapshot          - Get current snapshot
        4. version           - Get version info
        5. health            - Get health summary
        6. history           - Get snapshot history
        7. diff              - Compare last two snapshots
        8. statistics        - Get registry statistics
        9. latest_sync       - Get the last sync summary
        10. summary          - Full sync summary

    All DTO-only.
    """

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    @property
    def query_count(self) -> int:
        """Get total number of query types available."""
        return 10

    def runtime_state(self) -> Dict[str, Any]:
        """Get current runtime state."""
        return {
            "query": "runtime_state",
            "timestamp": datetime.now().timestamp(),
            "state": self._runtime.synchronizer.create_sync_summary(),
        }

    def registry(self) -> Dict[str, Any]:
        """List all registered runtimes."""
        runtimes = self._runtime.registry.list()
        return {
            "query": "registry",
            "timestamp": datetime.now().timestamp(),
            "count": len(runtimes),
            "runtimes": [s.to_dict() for s in runtimes],
        }

    def snapshot(self) -> Dict[str, Any]:
        """Get the current registry snapshot."""
        snap = self._runtime.registry.snapshot()
        return {
            "query": "snapshot",
            "timestamp": datetime.now().timestamp(),
            "snapshot": snap.to_dict(),
        }

    def version(self) -> Dict[str, Any]:
        """Get version information."""
        runtimes = self._runtime.registry.list()
        versions = {}
        for s in runtimes:
            v = str(s.version)
            if v not in versions:
                versions[v] = []
            versions[v].append(s.runtime_id)
        return {
            "query": "version",
            "timestamp": datetime.now().timestamp(),
            "current_version": str(RuntimeVersion.current()),
            "versions": versions,
        }

    def health(self) -> Dict[str, Any]:
        """Get health summary of all runtimes."""
        runtimes = self._runtime.registry.list()
        health_counts: Dict[str, int] = {}
        unhealthy: List[str] = []
        for s in runtimes:
            h = s.health.name
            health_counts[h] = health_counts.get(h, 0) + 1
            if h in ("DEGRADED", "CRITICAL"):
                unhealthy.append(s.runtime_id)
        return {
            "query": "health",
            "timestamp": datetime.now().timestamp(),
            "total": len(runtimes),
            "health_counts": health_counts,
            "unhealthy": unhealthy,
        }

    def history(self, limit: int = 10) -> Dict[str, Any]:
        """Get snapshot history."""
        snaps = self._runtime.snapshot_manager.history
        recent = snaps[-limit:] if limit > 0 else snaps
        return {
            "query": "history",
            "timestamp": datetime.now().timestamp(),
            "total": len(snaps),
            "returned": len(recent),
            "snapshots": [s.to_dict() for s in recent],
        }

    def diff(self) -> Dict[str, Any]:
        """Compare the last two snapshots."""
        diff_result = self._runtime.snapshot_manager.diff()
        return {
            "query": "diff",
            "timestamp": datetime.now().timestamp(),
            "diff": diff_result,
        }

    def statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        stats = self._runtime.registry.statistics()
        return {
            "query": "statistics",
            "timestamp": datetime.now().timestamp(),
            "statistics": stats,
        }

    def latest_sync(self) -> Dict[str, Any]:
        """Get the last synchronization summary."""
        summary = self._runtime.synchronizer.last_summary
        if summary is None:
            return {
                "query": "latest_sync",
                "timestamp": datetime.now().timestamp(),
                "has_sync": False,
            }
        return {
            "query": "latest_sync",
            "timestamp": datetime.now().timestamp(),
            "has_sync": True,
            "summary": summary,
        }

    def summary(self) -> Dict[str, Any]:
        """Get full synchronization summary."""
        return {
            "query": "summary",
            "timestamp": datetime.now().timestamp(),
            "registry_count": self._runtime.registry.count,
            "snapshot_count": self._runtime.snapshot_manager.count,
            "sync_count": self._runtime.synchronizer.sync_count,
            "consistent": self._runtime.validator.is_consistent(),
            "registry_stats": self._runtime.registry.statistics(),
            "latest_sync": (
                self._runtime.synchronizer.last_summary
                if self._runtime.synchronizer.last_summary
                else None
            ),
        }
