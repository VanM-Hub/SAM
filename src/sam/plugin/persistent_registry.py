"""
Persistent Plugin Registry – SQLite-backed plugin registry with optional in-memory cache.

Implements the same interface as PluginRegistry (in-memory) but persists
all plugin data to SQLite via PluginRepository.
"""

from __future__ import annotations

import time
import aiosqlite
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog

from .models import PluginManifest, PluginStatus
from .repository import PluginRepository, _normalize_status
from .registry import PluginDescriptor


@dataclass
class _CacheEntry:
    """Internal cache entry with timestamp."""
    value: Any
    timestamp: float = field(default_factory=time.time)


class PersistentPluginRegistry:
    """
    SQLite-backed plugin registry with optional in-memory cache.

    Implements the same interface as PluginRegistry (in-memory) but persists
    all plugin data to SQLite via PluginRepository.
    """

    def __init__(
        self,
        repository: PluginRepository,
        cache_ttl: Optional[int] = None,
    ) -> None:
        """
        Initialize the persistent registry.

        Args:
            repository: PluginRepository instance for DB persistence
            cache_ttl: Optional cache TTL in seconds. None = no cache.
        """
        self._repository = repository
        self._cache_ttl = cache_ttl
        self._cache: Dict[str, _CacheEntry] = {}
        self._list_cache: Dict[str, _CacheEntry] = {}
        self._logger = structlog.get_logger()

    def _invalidate_cache(self, plugin_id: Optional[str] = None) -> None:
        """Invalidate cache entries."""
        if plugin_id:
            self._cache.pop(f"manifest:{plugin_id}", None)
            self._cache.pop(f"descriptor:{plugin_id}", None)
        # Always invalidate list cache on any mutation
        self._list_cache.clear()

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache if valid."""
        if self._cache_ttl is None:
            return None
        entry = self._cache.get(key)
        if entry and (time.time() - entry.timestamp) < self._cache_ttl:
            return entry.value
        self._cache.pop(key, None)
        return None

    def _set_cached(self, key: str, value: Any) -> None:
        """Set value in cache."""
        if self._cache_ttl is not None:
            self._cache[key] = _CacheEntry(value)

    def _get_list_cached(self, key: str) -> Optional[Any]:
        """Get list from cache if valid."""
        if self._cache_ttl is None:
            return None
        entry = self._list_cache.get(key)
        if entry and (time.time() - entry.timestamp) < self._cache_ttl:
            return entry.value
        self._list_cache.pop(key, None)
        return None

    def _set_list_cached(self, key: str, value: Any) -> None:
        """Set list in cache."""
        if self._cache_ttl is not None:
            self._list_cache[key] = _CacheEntry(value)

    def _descriptor_from_manifest(self, manifest: PluginManifest, status: Optional[PluginStatus] = None) -> PluginDescriptor:
        """Create PluginDescriptor from manifest with optional status."""
        return PluginDescriptor(
            manifest=manifest,
            status=status or PluginStatus.INSTALLED,
        )

    async def register(self, manifest: PluginManifest) -> str:
        """
        Register a plugin manifest (persist to DB).

        Args:
            manifest: PluginManifest instance

        Returns:
            plugin_id (str)

        Raises:
            ValueError: If plugin already registered
        """
        plugin_id = manifest.id or manifest.name

        # Check if already exists
        existing = await self._repository.get(plugin_id)
        if existing:
            self._logger.warning(
                "plugin_already_registered",
                plugin_id=plugin_id,
                name=manifest.name
            )
            raise ValueError(f"Plugin already registered: {plugin_id}")

        # Persist to database
        await self._repository.create(manifest)

        # Invalidate cache
        self._invalidate_cache(plugin_id)

        self._logger.info(
            "plugin_registered",
            plugin_id=plugin_id,
            name=manifest.name,
            version=manifest.version,
            capabilities=manifest.capabilities
        )
        return plugin_id

    async def get(self, plugin_id: str) -> Optional[PluginManifest]:
        """Get plugin manifest by ID."""
        # Check cache
        cached = self._get_cached(f"manifest:{plugin_id}")
        if cached is not None:
            return cached

        # Fetch from repository
        manifest = await self._repository.get(plugin_id)

        # Cache result
        self._set_cached(f"manifest:{plugin_id}", manifest)

        return manifest

    async def _get_status_from_db(self, plugin_id: str) -> Optional[PluginStatus]:
        """Get plugin status from database directly."""
        async with aiosqlite.connect(self._repository.db_path, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT status FROM plugins WHERE plugin_id = ?", (plugin_id,)
            )
            row = await cursor.fetchone()
            if row and row["status"]:
                normalized = _normalize_status(row["status"])
                try:
                    return PluginStatus(normalized)
                except ValueError:
                    return PluginStatus.INSTALLED
        return None

    async def get_descriptor(self, plugin_id: str) -> Optional[PluginDescriptor]:
        """Get full plugin descriptor by ID."""
        # Check cache
        cached = self._get_cached(f"descriptor:{plugin_id}")
        if cached is not None:
            return cached

        manifest = await self._repository.get(plugin_id)
        if not manifest:
            return None

        # Get status from database
        status = await self._get_status_from_db(plugin_id)
        if status is None:
            status = PluginStatus.INSTALLED

        descriptor = self._descriptor_from_manifest(manifest, status)

        # Cache result
        self._set_cached(f"descriptor:{plugin_id}", descriptor)

        return descriptor

    async def list(self, status: Optional[PluginStatus] = None) -> List[PluginManifest]:
        """
        List all registered plugins, optionally filtered by status.

        Args:
            status: Filter by PluginStatus

        Returns:
            List of PluginManifest
        """
        cache_key = f"list:{status.value if status else 'all'}"

        # Check cache
        cached = self._get_list_cached(cache_key)
        if cached is not None:
            return cached

        # Fetch from repository
        manifests = await self._repository.list(status)

        # Cache result
        self._set_list_cached(cache_key, manifests)

        return manifests

    async def list_descriptors(self, status: Optional[PluginStatus] = None) -> List[PluginDescriptor]:
        """List full plugin descriptors, optionally filtered by status."""
        cache_key = f"descriptors:{status.value if status else 'all'}"

        # Check cache
        cached = self._get_list_cached(cache_key)
        if cached is not None:
            return cached

        manifests = await self._repository.list(status)
        descriptors = []
        for manifest in manifests:
            st = await self._get_status_from_db(manifest.id)
            if st is None:
                st = PluginStatus.INSTALLED
            descriptors.append(self._descriptor_from_manifest(manifest, st))

        # Cache result
        self._set_list_cached(cache_key, descriptors)

        return descriptors

    async def update_status(
        self,
        plugin_id: str,
        status: PluginStatus,
        error: Optional[str] = None
    ) -> None:
        """
        Update plugin lifecycle status.

        Args:
            plugin_id: Plugin identifier
            status: New PluginStatus
            error: Optional error message

        Raises:
            ValueError: If plugin not found
        """
        # Verify plugin exists
        existing = await self._repository.get(plugin_id)
        if not existing:
            self._logger.error("plugin_not_found", plugin_id=plugin_id)
            raise ValueError(f"Plugin not found: {plugin_id}")

        # Update in repository (repository.update handles status normalization)
        await self._repository.update(plugin_id, {"status": status})

        # Invalidate cache
        self._invalidate_cache(plugin_id)

        self._logger.info(
            "plugin_status_updated",
            plugin_id=plugin_id,
            new_status=status.value if hasattr(status, 'value') else str(status),
            error=error
        )

    async def unregister(self, plugin_id: str) -> None:
        """Remove plugin from registry."""
        # Verify plugin exists
        existing = await self._repository.get(plugin_id)
        if existing:
            manifest = existing
            await self._repository.delete(plugin_id)
            self._logger.info(
                "plugin_unregistered",
                plugin_id=plugin_id,
                name=manifest.name
            )
        else:
            self._logger.warning("plugin_not_found_for_unregister", plugin_id=plugin_id)

        # Invalidate cache
        self._invalidate_cache(plugin_id)

    async def get_by_capability(self, capability_id: str) -> List[PluginDescriptor]:
        """Find plugins that provide a specific capability."""
        cache_key = f"capability:{capability_id}"

        # Check cache
        cached = self._get_list_cached(cache_key)
        if cached is not None:
            return cached

        # Fetch all plugins and filter by capability
        all_plugins = await self._repository.list()
        result = []
        for manifest in all_plugins:
            if capability_id in manifest.capabilities:
                st = await self._get_status_from_db(manifest.id)
                if st is None:
                    st = PluginStatus.INSTALLED
                result.append(self._descriptor_from_manifest(manifest, st))

        # Cache result
        self._set_list_cached(cache_key, result)

        return result

    async def install_from_manifest(self, manifest: PluginManifest) -> str:
        """
        Install a plugin from manifest (alias for register with INSTALLED status).

        Args:
            manifest: PluginManifest instance

        Returns:
            plugin_id (str)
        """
        # Register with INSTALLED status (handled by repository.create)
        plugin_id = await self.register(manifest)
        return plugin_id

    async def enable(self, plugin_id: str) -> None:
        """Enable a registered plugin."""
        await self.update_status(plugin_id, PluginStatus.ENABLED)

    async def disable(self, plugin_id: str) -> None:
        """Disable an enabled plugin."""
        await self.update_status(plugin_id, PluginStatus.DISABLED)

    async def get_plugin(self, plugin_id: str) -> Optional[PluginManifest]:
        """Alias for get (for CLI compatibility)."""
        return await self.get(plugin_id)

    async def list_plugins(self, status: Optional[PluginStatus] = None) -> List[PluginManifest]:
        """Alias for list (for CLI compatibility)."""
        return await self.list(status)

    async def uninstall(self, plugin_id: str) -> None:
        """Uninstall a plugin completely."""
        await self.unregister(plugin_id)

    async def count(self) -> int:
        """Get total number of registered plugins."""
        all_plugins = await self._repository.list()
        return len(all_plugins)

    async def clear(self) -> None:
        """Clear all plugins (for testing)."""
        all_plugins = await self._repository.list()
        for plugin in all_plugins:
            await self._repository.delete(plugin.id)
        self._cache.clear()
        self._list_cache.clear()
        self._logger.info("plugin_registry_cleared")


async def create_plugin_registry(db_path: str, cache_ttl: Optional[int] = None) -> PersistentPluginRegistry:
    """
    Factory function to create a PersistentPluginRegistry instance.

    Args:
        db_path: Path to SQLite database
        cache_ttl: Optional cache TTL in seconds

    Returns:
        PersistentPluginRegistry instance
    """
    repository = PluginRepository(db_path)
    return PersistentPluginRegistry(repository, cache_ttl)