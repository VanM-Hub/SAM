"""
Guardian Runtime Synchronizer.

Synchronizes runtime state through the event pipeline.
Synchronous only. No async, no threading, no network.

Pipeline:
    GuardianEvent → Runtime Registry → Snapshot Builder
    → Version Check → Synchronize → Summary
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict

from .event import GuardianEvent, GuardianEventType, GuardianEventPriority
from .state import (
    RuntimeState,
    RuntimeStatus,
    RuntimeHealth,
    RuntimeVersion,
    RuntimeStatistics,
    RuntimeSnapshot,
)
from .registry import GuardianRuntimeRegistry


class GuardianRuntimeSynchronizer:
    """
    Synchronous runtime synchronizer for Guardian Live.

    Processes events and updates runtime state through
    the registry. Produces sync summaries.
    """

    def __init__(self, registry: GuardianRuntimeRegistry) -> None:
        self._registry = registry
        self._sync_count: int = 0
        self._last_summary: Optional[Dict[str, Any]] = None
        self._current_runtime_id: Optional[str] = None

    @property
    def sync_count(self) -> int:
        """Get total number of synchronizations performed."""
        return self._sync_count

    @property
    def last_summary(self) -> Optional[Dict[str, Any]]:
        """Get the last synchronization summary."""
        return self._last_summary

    def set_runtime_id(self, runtime_id: str) -> None:
        """Set the current runtime ID for this synchronizer."""
        self._current_runtime_id = runtime_id

    @property
    def current_runtime_id(self) -> Optional[str]:
        """Get the current runtime ID."""
        return self._current_runtime_id

    @property
    def registry(self) -> GuardianRuntimeRegistry:
        """Get the underlying registry."""
        return self._registry

    def register_current(self, metadata: Optional[Dict[str, str]] = None) -> RuntimeState:
        """
        Register the current runtime if not already registered.

        Args:
            metadata: Optional metadata.

        Returns:
            The RuntimeState for the current runtime.
        """
        if self._current_runtime_id and not self._registry.exists(self._current_runtime_id):
            return self._registry.register(
                runtime_id=self._current_runtime_id,
                metadata=metadata,
            )
        state = self._registry.lookup(self._current_runtime_id) if self._current_runtime_id else None
        if state is None:
            raise ValueError("Current runtime ID not set and runtime not registered.")
        return state

    def synchronize(self, event: GuardianEvent) -> Dict[str, Any]:
        """
        Execute a synchronization cycle from an event.

        Pipeline:
            1. Ensure current runtime is registered
            2. Build snapshot from registry
            3. Check versions
            4. Produce summary

        Args:
            event: The event triggering synchronization.

        Returns:
            Dict with synchronization summary.
        """
        self._sync_count += 1

        # 1. Ensure current runtime is registered
        if self._current_runtime_id and not self._registry.exists(self._current_runtime_id):
            self._registry.register(
                runtime_id=self._current_runtime_id,
                metadata={"source": event.metadata.source.name},
            )

        # 2. Update current runtime state
        if self._current_runtime_id:
            current = self._registry.lookup(self._current_runtime_id)
            if current:
                new_stats = RuntimeStatistics(
                    total_dispatched=current.statistics.total_dispatched + 1,
                    subscriber_count=current.statistics.subscriber_count,
                    error_count=current.statistics.error_count,
                    history_count=current.statistics.history_count,
                    trigger_count=current.statistics.trigger_count,
                    feed_count=current.statistics.feed_count,
                    preview_count=current.statistics.preview_count,
                    timestamp=datetime.now().timestamp(),
                )
                self._registry.update_state(
                    self._current_runtime_id,
                    statistics=new_stats,
                )

        # 3. Build snapshot
        snapshot = self._registry.snapshot()

        # 4. Version check
        version_check = self._check_versions(snapshot)

        # 5. Build summary
        summary = {
            "sync_id": str(uuid.uuid4()),
            "sync_count": self._sync_count,
            "timestamp": datetime.now().timestamp(),
            "trigger_event": event.metadata.event_type.name,
            "trigger_source": event.metadata.source.name,
            "runtime_count": snapshot.total_runtimes,
            "runtimes": [
                {
                    "id": s.runtime_id,
                    "version": str(s.version),
                    "status": s.status.name,
                    "health": s.health.name,
                }
                for s in snapshot.runtimes.values()
            ],
            "version_check": version_check,
            "statistics": snapshot.statistics.to_dict(),
        }
        self._last_summary = summary
        return summary

    def _check_versions(self, snapshot: RuntimeSnapshot) -> Dict[str, Any]:
        """
        Check version consistency across all runtimes.

        Args:
            snapshot: Current runtime snapshot.

        Returns:
            Dict with version consistency info.
        """
        versions: Dict[str, int] = defaultdict(int)
        mismatches: List[str] = []

        for state in snapshot.runtimes.values():
            version_str = str(state.version)
            versions[version_str] += 1

        current_version_str = str(RuntimeVersion.current())
        for state in snapshot.runtimes.values():
            if str(state.version) != current_version_str:
                mismatches.append(
                    f"{state.runtime_id}: version {str(state.version)} "
                    f"(expected {current_version_str})"
                )

        return {
            "current_version": current_version_str,
            "version_counts": dict(versions),
            "all_matching": len(mismatches) == 0,
            "mismatches": mismatches,
        }

    def create_sync_summary(self) -> Dict[str, Any]:
        """
        Create a synchronization summary without triggering a cycle.

        Returns:
            Dict with current sync summary.
        """
        snapshot = self._registry.snapshot()
        version_check = self._check_versions(snapshot)
        return {
            "sync_id": str(uuid.uuid4()),
            "sync_count": self._sync_count,
            "timestamp": datetime.now().timestamp(),
            "runtime_count": snapshot.total_runtimes,
            "version_check": version_check,
            "statistics": snapshot.statistics.to_dict(),
        }
