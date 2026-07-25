"""Plugin Discovery - automatic discovery and installation of plugins from various sources."""

from __future__ import annotations

import structlog
from pathlib import Path
from typing import List, Optional

from sam.plugin.loader import PluginManifestLoader
from sam.plugin.repository import PluginRepository
from sam.plugin.registry import PluginRegistry
from sam.plugin.models import PluginManifest


logger = structlog.get_logger()


class PluginDiscovery:
    """Discovers and installs plugins from various sources."""

    def __init__(
        self,
        registry: PluginRegistry,
        repository: PluginRepository,
    ) -> None:
        self.registry = registry
        self.repository = repository
        self.loader = PluginManifestLoader()

    async def discover_from_directory(self, directory: Path) -> List[str]:
        """Discover and install plugins from a directory.

        Scans for manifest.yaml or manifest.json files recursively.
        For each plugin found, installs, registers, and enables it.
        """
        manifests = self.loader.load_from_directory(directory)
        plugin_ids = []

        for manifest in manifests:
            # Check if already installed
            existing = await self.repository.get_by_name(manifest.name)
            if existing:
                logger.info("plugin_already_installed", name=manifest.name)
                continue

            # Install and register (install_from_manifest handles registration)
            plugin_id = await self.registry.install_from_manifest(manifest)
            # Enable the plugin
            await self.registry.enable(plugin_id)

            plugin_ids.append(plugin_id)
            logger.info("plugin_discovered_and_enabled", name=manifest.name, id=plugin_id)

        return plugin_ids

    async def discover_from_registry(self) -> List[str]:
        """Discover plugins from a remote registry/index.

        Placeholder for future marketplace integration.
        """
        # Future: query plugin marketplace API
        return []

    async def discover_all(self, plugins_dir: Optional[Path] = None) -> List[str]:
        """Discover plugins from all sources.

        Currently only supports directory-based discovery.
        Future: registry/API-based discovery.
        """
        all_plugins = []

        if plugins_dir and plugins_dir.exists():
            all_plugins.extend(await self.discover_from_directory(plugins_dir))

        # Future: discover from registry
        # all_plugins.extend(await self.discover_from_registry())

        return all_plugins


async def create_plugin_discovery(
    db_path: str,
    plugin_registry: PluginRegistry,
) -> PluginDiscovery:
    """Factory function to create a PluginDiscovery instance."""
    repository = PluginRepository(db_path)
    return PluginDiscovery(plugin_registry, repository)