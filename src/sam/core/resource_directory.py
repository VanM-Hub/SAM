"""Runtime Directory — resource registry yang diperkaya dengan watch, subscribe, query, dan
kemampuan ownership discovery.

Extends ResourceManager dengan:
- watch/subscribe: notifikasi perubahan resource via callback
- query: filter resources dengan dict fleksibel
- find_owner / find_orphans: ownership discovery
- EventBus integration: publish event tiap perubahan
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

import structlog

from .resource import (
    RuntimeResource,
    ResourceType,
    ResourceStatus,
    ResourceOwner,
    ResourceNotFoundError,
)
from .resource_manager import ResourceManager
from .event_bus import EventBus
from .events import Event

# ── Directory event types ────────────────────────────────────────────

RESOURCE_REGISTERED = "resource.registered"
RESOURCE_STATUS_CHANGED = "resource.status_changed"
RESOURCE_DATA_CHANGED = "resource.data_changed"
RESOURCE_OWNER_CHANGED = "resource.owner_changed"
RESOURCE_ORPHAN_RECOVERED = "resource.orphan_recovered"


# ── Error classes ────────────────────────────────────────────────────

class DirectoryError(RuntimeError):
    """Base error untuk Runtime Directory."""


class SubscriptionNotFoundError(DirectoryError):
    """Subscription pattern tidak ditemukan."""
    def __init__(self, pattern: str):
        self.pattern = pattern
        super().__init__(f"Subscription not found for pattern: {pattern}")


# ── Resource Directory ───────────────────────────────────────────────

class ResourceDirectory(ResourceManager):
    """Runtime Directory — resource registry with watch/subscribe/query.

    Extends ResourceManager dengan kemampuan directory:
    - watch: callback per resource type
    - subscribe: callback dengan pattern matching
    - query: filter resources dengan dict fleksibel
    - find_owner / find_orphans
    - EventBus publishing untuk setiap state change
    """

    def __init__(self, db, event_bus: Optional[EventBus] = None):
        super().__init__(db)
        self._event_bus = event_bus
        self._watchers: Dict[str, List[Callable[[RuntimeResource], Any]]] = {}
        self._subscriptions: Dict[str, List[Callable[[RuntimeResource, str], Any]]] = {}
        self._logger = structlog.get_logger()

    # ── Override: register with event ────────────────────────────────

    async def register(self, resource: RuntimeResource) -> None:
        await super().register(resource)
        await self._publish_event(RESOURCE_REGISTERED, resource)
        await self._notify_watchers(resource, RESOURCE_REGISTERED)

    async def update_status(
        self, resource_id: str, status: ResourceStatus
    ) -> RuntimeResource:
        updated = await super().update_status(resource_id, status)
        await self._publish_event(RESOURCE_STATUS_CHANGED, updated)
        await self._notify_watchers(updated, RESOURCE_STATUS_CHANGED)
        return updated

    async def update_data(
        self, resource_id: str, data: Dict[str, Any], version: int
    ) -> RuntimeResource:
        updated = await super().update_data(resource_id, data, version)
        await self._publish_event(RESOURCE_DATA_CHANGED, updated)
        await self._notify_watchers(updated, RESOURCE_DATA_CHANGED)
        return updated

    async def claim(
        self, resource_id: str, node_id: str, lease_seconds: int
    ) -> bool:
        result = await super().claim(resource_id, node_id, lease_seconds)
        resource = await self.get(resource_id)
        if resource:
            await self._publish_event(RESOURCE_OWNER_CHANGED, resource)
            await self._notify_watchers(resource, RESOURCE_OWNER_CHANGED)
        return result

    async def release(self, resource_id: str, node_id: str) -> None:
        await super().release(resource_id, node_id)
        resource = await self.get(resource_id)
        if resource:
            await self._publish_event(RESOURCE_OWNER_CHANGED, resource)
            await self._notify_watchers(resource, RESOURCE_OWNER_CHANGED)

    async def recover_orphaned(
        self, timeout_seconds: int = 60
    ) -> List[RuntimeResource]:
        orphaned = await super().recover_orphaned(timeout_seconds)
        if orphaned:
            await self._publish_event(RESOURCE_ORPHAN_RECOVERED, orphaned[0])
            for res in orphaned:
                await self._notify_watchers(res, RESOURCE_ORPHAN_RECOVERED)
        return orphaned

    # ── Watch API ────────────────────────────────────────────────────

    async def watch(
        self, resource_type: ResourceType, callback: Callable[[RuntimeResource], Any]
    ) -> None:
        """Subscribe callback terhadap semua perubahan resource type tertentu.

        Args:
            resource_type: Jenis resource yang dipantau.
            callback: Fungsi yang dipanggil dengan resource yang berubah.
        """
        type_key = resource_type.value if isinstance(resource_type, ResourceType) else resource_type
        if type_key not in self._watchers:
            self._watchers[type_key] = []
        self._watchers[type_key].append(callback)
        self._logger.debug("watcher_registered", resource_type=type_key)

    async def unwatch(
        self, resource_type: ResourceType, callback: Callable[[RuntimeResource], Any]
    ) -> None:
        """Hapus watch callback."""
        type_key = resource_type.value if isinstance(resource_type, ResourceType) else resource_type
        if type_key in self._watchers:
            self._watchers[type_key] = [
                cb for cb in self._watchers[type_key] if cb != callback
            ]
            if not self._watchers[type_key]:
                del self._watchers[type_key]

    # ── Subscribe API ────────────────────────────────────────────────

    async def subscribe(
        self, pattern: str, callback: Callable[[RuntimeResource, str], Any]
    ) -> None:
        """Subscribe callback dengan pattern pada event resource.

        Args:
            pattern: Pattern event (misal "resource.*", "resource.status_changed").
            callback: Fungsi callback(resource, event_type).
        """
        if pattern not in self._subscriptions:
            self._subscriptions[pattern] = []
        self._subscriptions[pattern].append(callback)
        self._logger.debug("subscription_added", pattern=pattern)

    async def unsubscribe(self, pattern: str) -> None:
        """Hapus semua callback untuk pattern tertentu."""
        if pattern not in self._subscriptions:
            raise SubscriptionNotFoundError(pattern)
        del self._subscriptions[pattern]
        self._logger.debug("subscription_removed", pattern=pattern)

    # ── Query API ────────────────────────────────────────────────────

    async def query(self, filters: Dict[str, Any]) -> List[RuntimeResource]:
        """Query resources dengan filter dict fleksibel.

        Supported filter keys:
          - type: ResourceType atau string (equality)
          - status: ResourceStatus atau string (equality)
          - name: string (equality)
          - owner_node_id: string (equality)
          - owned: bool (True=has owner, False=no owner)
          - orphaned: bool (True=has expired lease)

        Args:
            filters: Dict of filter key → value.

        Returns:
            List of matching RuntimeResources.
        """
        all_resources = await self.list()

        results: List[RuntimeResource] = []
        for res in all_resources:
            if self._match_filters(res, filters):
                results.append(res)

        return results

    # ── Ownership discovery ──────────────────────────────────────────

    async def find_owner(self, resource_id: str) -> Optional[ResourceOwner]:
        """Cari owner dari sebuah resource.

        Returns:
            ResourceOwner jika resource memiliki owner, None jika tidak.
        """
        resource = await self.get(resource_id)
        if not resource:
            raise ResourceNotFoundError(resource_id)
        return resource.owner

    async def find_orphans(self, timeout_seconds: int = 60) -> List[RuntimeResource]:
        """Temukan semua resource orphan (lease expired).

        Alias semantic untuk recover_orphaned — hanya membaca, tidak
        mengubah ownership. Untuk recovery sejati, panggil recover_orphaned().

        Args:
            timeout_seconds: Threshold detik sejak lease expired.

        Returns:
            List of orphaned RuntimeResource (ownership masih intact).
        """
        all_resources = await self.list()
        now = datetime.utcnow()
        orphans: List[RuntimeResource] = []

        for res in all_resources:
            if res.owner is None:
                continue
            if res.owner.is_expired:
                orphans.append(res)

        return orphans

    # ── Helpers ──────────────────────────────────────────────────────

    def _match_filters(self, resource: RuntimeResource, filters: Dict[str, Any]) -> bool:
        """Check apakah resource cocok dengan semua filter."""
        for key, value in filters.items():
            if key == "type":
                expected = value.value if isinstance(value, ResourceType) else value
                actual = resource.type.value if isinstance(resource.type, ResourceType) else resource.type
                if actual != expected:
                    return False

            elif key == "status":
                expected = value.value if isinstance(value, ResourceStatus) else value
                actual = resource.status.value if isinstance(resource.status, ResourceStatus) else resource.status
                if actual != expected:
                    return False

            elif key == "name":
                if resource.name != value:
                    return False

            elif key == "owner_node_id":
                if resource.owner is None or resource.owner.node_id != value:
                    return False

            elif key == "owned":
                if value and resource.owner is None:
                    return False
                if not value and resource.owner is not None:
                    return False

            elif key == "orphaned":
                if value and not resource.is_orphaned:
                    return False
                if not value and resource.is_orphaned:
                    return False

            # Unknown key → tidak match
            else:
                return False

        return True

    def _event_type_matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Match event_type terhadap pattern (wildcard * support)."""
        if pattern == "*":
            return True
        if pattern == event_type:
            return True
        # Pattern seperti "resource.*" match "resource.registered" dll.
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            if event_type.startswith(prefix):
                return True
        return False

    async def _notify_watchers(
        self, resource: RuntimeResource, event_type: str
    ) -> None:
        """Notify watchers dan subscriptions tentang perubahan."""
        # Type watchers
        type_key = resource.type.value if isinstance(resource.type, ResourceType) else resource.type
        if type_key in self._watchers:
            for cb in self._watchers[type_key]:
                try:
                    result = cb(resource)
                    if hasattr(result, "__await__"):
                        await result
                except Exception as e:
                    self._logger.error(
                        "watcher_error",
                        resource_type=type_key,
                        error=str(e),
                    )

        # Pattern subscriptions
        for pattern, callbacks in self._subscriptions.items():
            if self._event_type_matches_pattern(event_type, pattern):
                for cb in callbacks:
                    try:
                        result = cb(resource, event_type)
                        if hasattr(result, "__await__"):
                            await result
                    except Exception as e:
                        self._logger.error(
                            "subscription_error",
                            pattern=pattern,
                            error=str(e),
                        )

    async def _publish_event(
        self, event_type: str, resource: RuntimeResource
    ) -> None:
        """Publish event ke EventBus."""
        if self._event_bus is None:
            return
        import uuid

        await self._event_bus.publish(Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source="resource_directory",
            payload={
                "resource_id": resource.id,
                "resource_type": resource.type.value if isinstance(resource.type, ResourceType) else resource.type,
                "resource_name": resource.name,
                "status": resource.status.value if isinstance(resource.status, ResourceStatus) else resource.status,
            },
        ))
