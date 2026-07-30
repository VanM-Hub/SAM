"""
Guardian Runtime Registry.

Manages registration and lookup of runtime instances.
Synchronous only. No async, no threading, no network.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

from .state import (
    RuntimeState,
    RuntimeStatus,
    RuntimeHealth,
    RuntimeVersion,
    RuntimeStatistics,
    RuntimeSnapshot,
)


class GuardianRuntimeRegistry:
    """
    Synchronous registry for Guardian runtime instances.

    Provides register, unregister, lookup, list, snapshot,
    and statistics operations.
    """

    def __init__(self) -> None:
        self._runtimes: Dict[str, RuntimeState] = {}
        self._registration_order: List[str] = []

    def register(
        self,
        runtime_id: str,
        version: Optional[RuntimeVersion] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> RuntimeState:
        """
        Register a runtime instance.

        Args:
            runtime_id: Unique identifier for the runtime.
            version: Runtime version (default: current).
            metadata: Optional metadata key-value pairs.

        Returns:
            The registered RuntimeState.
        """
        state = RuntimeState(
            runtime_id=runtime_id,
            version=version or RuntimeVersion.current(),
            health=RuntimeHealth.HEALTHY,
            status=RuntimeStatus.RUNNING,
            statistics=RuntimeStatistics.empty(),
            last_sync_at=datetime.now().timestamp(),
            metadata=metadata or {},
        )
        self._runtimes[runtime_id] = state
        if runtime_id not in self._registration_order:
            self._registration_order.append(runtime_id)
        return state

    def unregister(self, runtime_id: str) -> bool:
        """
        Unregister a runtime instance.

        Args:
            runtime_id: The runtime ID to remove.

        Returns:
            True if removed, False if not found.
        """
        if runtime_id in self._runtimes:
            del self._runtimes[runtime_id]
            if runtime_id in self._registration_order:
                self._registration_order.remove(runtime_id)
            return True
        return False

    def lookup(self, runtime_id: str) -> Optional[RuntimeState]:
        """
        Look up a runtime by ID.

        Args:
            runtime_id: The runtime ID to find.

        Returns:
            RuntimeState if found, None otherwise.
        """
        return self._runtimes.get(runtime_id)

    def update_state(self, runtime_id: str, **updates) -> Optional[RuntimeState]:
        """
        Update a runtime's state immutably.

        Creates a new RuntimeState with updated fields.
        Does NOT modify the original.

        Args:
            runtime_id: The runtime ID to update.
            **updates: Fields to update (status, health, etc.).

        Returns:
            New RuntimeState if found, None otherwise.
        """
        current = self._runtimes.get(runtime_id)
        if current is None:
            return None

        new_statistics = current.statistics
        if "statistics" in updates:
            new_statistics = updates.pop("statistics")

        new_state = RuntimeState(
            runtime_id=current.runtime_id,
            version=updates.pop("version", current.version),
            health=updates.pop("health", current.health),
            status=updates.pop("status", current.status),
            statistics=new_statistics,
            last_sync_at=datetime.now().timestamp(),
            metadata=updates.pop("metadata", current.metadata),
        )
        self._runtimes[runtime_id] = new_state
        return new_state

    def list(self) -> List[RuntimeState]:
        """
        List all registered runtimes.

        Returns:
            List of RuntimeState in registration order.
        """
        return [
            self._runtimes[rid]
            for rid in self._registration_order
            if rid in self._runtimes
        ]

    @property
    def count(self) -> int:
        """Get the number of registered runtimes."""
        return len(self._runtimes)

    @property
    def ids(self) -> List[str]:
        """Get all registered runtime IDs."""
        return list(self._registration_order)

    def exists(self, runtime_id: str) -> bool:
        """Check if a runtime ID is registered."""
        return runtime_id in self._runtimes

    def clear(self) -> None:
        """Remove all registered runtimes."""
        self._runtimes.clear()
        self._registration_order.clear()

    def snapshot(self) -> RuntimeSnapshot:
        """
        Create an aggregate snapshot of all registered runtimes.

        Returns:
            RuntimeSnapshot with all current runtime states.
        """
        runtimes = dict(self._runtimes)
        errors: List[str] = []
        total_dispatched = 0
        subscriber_count = 0
        error_count = 0
        history_count = 0

        for state in runtimes.values():
            total_dispatched += state.statistics.total_dispatched
            subscriber_count += state.statistics.subscriber_count
            error_count += state.statistics.error_count
            history_count += state.statistics.history_count

        stats = RuntimeStatistics(
            total_dispatched=total_dispatched,
            subscriber_count=subscriber_count,
            error_count=error_count,
            history_count=history_count,
            timestamp=datetime.now().timestamp(),
        )

        return RuntimeSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            total_runtimes=len(runtimes),
            runtimes=runtimes,
            statistics=stats,
            errors=errors,
        )

    def statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dict with registry-level statistics.
        """
        snap = self.snapshot()
        versions: Dict[str, int] = defaultdict(int)
        statuses: Dict[str, int] = defaultdict(int)
        healths: Dict[str, int] = defaultdict(int)

        for state in snap.runtimes.values():
            versions[str(state.version)] += 1
            statuses[state.status.name] += 1
            healths[state.health.name] += 1

        return {
            "total_runtimes": snap.total_runtimes,
            "versions": dict(versions),
            "statuses": dict(statuses),
            "healths": dict(healths),
            "statistics": snap.statistics.to_dict(),
            "timestamp": snap.timestamp,
        }
