"""
Plugin Registry – manages plugin descriptors and lifecycle status.

Similar to CapabilityRegistry, but for plugins.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import structlog

from .models import PluginManifest, PluginStatus


@dataclass
class PluginDescriptor:
    """Internal descriptor for a registered plugin."""
    manifest: PluginManifest
    status: PluginStatus
    registered_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class PluginRegistry:
    """
    Registry for plugins – stores descriptors, not instances.

    Similar to CapabilityRegistry, this is a catalog of plugin metadata
    and lifecycle status.
    """

    def __init__(self):
        self._descriptors: Dict[str, PluginDescriptor] = {}
        self._logger = structlog.get_logger()

    async def register(self, manifest: PluginManifest) -> str:
        """
        Register a plugin manifest.

        Args:
            manifest: PluginManifest instance

        Returns:
            plugin_id (str)

        Raises:
            ValueError: If plugin already registered
        """
        plugin_id = manifest.id or manifest.name

        if plugin_id in self._descriptors:
            self._logger.warning(
                "plugin_already_registered",
                plugin_id=plugin_id,
                name=manifest.name
            )
            raise ValueError(f"Plugin already registered: {plugin_id}")

        descriptor = PluginDescriptor(
            manifest=manifest,
            status=PluginStatus.REGISTERED
        )
        self._descriptors[plugin_id] = descriptor

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
        descriptor = self._descriptors.get(plugin_id)
        if descriptor:
            return descriptor.manifest
        return None

    async def get_descriptor(self, plugin_id: str) -> Optional[PluginDescriptor]:
        """Get full plugin descriptor by ID."""
        return self._descriptors.get(plugin_id)

    async def list(self, status: Optional[PluginStatus] = None) -> List[PluginManifest]:
        """
        List all registered plugins, optionally filtered by status.

        Args:
            status: Filter by PluginStatus

        Returns:
            List of PluginManifest
        """
        manifests = []
        for plugin_id, descriptor in self._descriptors.items():
            if status is None or descriptor.status == status:
                manifests.append(descriptor.manifest)
        return manifests

    async def list_descriptors(self, status: Optional[PluginStatus] = None) -> List[PluginDescriptor]:
        """List full plugin descriptors, optionally filtered by status."""
        descriptors = []
        for plugin_id, descriptor in self._descriptors.items():
            if status is None or descriptor.status == status:
                descriptors.append(descriptor)
        return descriptors

    async def update_status(self, plugin_id: str, status: PluginStatus, error: Optional[str] = None) -> None:
        """
        Update plugin lifecycle status.

        Args:
            plugin_id: Plugin identifier
            status: New PluginStatus
            error: Optional error message

        Raises:
            ValueError: If plugin not found
        """
        descriptor = self._descriptors.get(plugin_id)
        if not descriptor:
            self._logger.error("plugin_not_found", plugin_id=plugin_id)
            raise ValueError(f"Plugin not found: {plugin_id}")

        old_status = descriptor.status
        descriptor.status = status
        descriptor.updated_at = datetime.utcnow()
        descriptor.error = error

        self._logger.info(
            "plugin_status_updated",
            plugin_id=plugin_id,
            old_status=old_status.value if hasattr(old_status, 'value') else str(old_status),
            new_status=status.value if hasattr(status, 'value') else str(status),
            error=error
        )

    async def unregister(self, plugin_id: str) -> None:
        """Remove plugin from registry."""
        if plugin_id in self._descriptors:
            manifest = self._descriptors[plugin_id].manifest
            del self._descriptors[plugin_id]
            self._logger.info(
                "plugin_unregistered",
                plugin_id=plugin_id,
                name=manifest.name
            )
        else:
            self._logger.warning("plugin_not_found_for_unregister", plugin_id=plugin_id)

    async def get_by_capability(self, capability_id: str) -> List[PluginDescriptor]:
        """Find plugins that provide a specific capability."""
        result = []
        for plugin_id, descriptor in self._descriptors.items():
            if capability_id in descriptor.manifest.capabilities:
                result.append(descriptor)
        return result

    async def count(self) -> int:
        """Get total number of registered plugins."""
        return len(self._descriptors)

    async def clear(self) -> None:
        """Clear all plugins (for testing)."""
        self._descriptors.clear()
        self._logger.info("plugin_registry_cleared")