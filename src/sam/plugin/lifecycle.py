"""
Plugin Lifecycle Manager

Manages plugin lifecycle from install -> uninstall.
"""

import asyncio
import importlib
import inspect
import structlog
from typing import Optional, Any
from pathlib import Path

from packaging.version import Version

from .models import PluginManifest, PluginStatus
from .loader import PluginManifestLoader
from .validator import PluginManifestValidator
from .registry import PluginRegistry
from .dependency import DependencyResolver


class PluginLifecycleManager:
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self.loader = PluginManifestLoader()
        self.validator = PluginManifestValidator()
        self.dependency_resolver = DependencyResolver(registry)
        self._logger = structlog.get_logger()

    async def install(self, manifest_or_path: Any) -> str:
        """Install a plugin from a PluginManifest or a path to manifest file.

        Returns plugin_id.
        """
        # Load manifest if path provided
        if isinstance(manifest_or_path, (str, Path)):
            path = Path(manifest_or_path)
            if not path.exists():
                raise FileNotFoundError(f"Manifest path not found: {path}")
            manifest = self.loader.load_from_yaml(path)
        elif isinstance(manifest_or_path, PluginManifest):
            manifest = manifest_or_path
        else:
            # assume raw dict
            manifest = PluginManifest(**manifest_or_path)

        plugin_id = manifest.id or manifest.name

        # Save to registry as INSTALLED
        await self.registry.register(manifest)
        await self.registry.update_status(plugin_id, PluginStatus.INSTALLED)
        self._logger.info("plugin_installed", plugin_id=plugin_id, name=manifest.name)
        return plugin_id

    async def validate(self, plugin_id: str) -> bool:
        """Validate manifest using PluginManifestValidator. Update status to VALIDATED on success."""
        descriptor = await self.registry.get_descriptor(plugin_id)
        if not descriptor:
            raise ValueError(f"Plugin not found: {plugin_id}")

        manifest = descriptor.manifest
        errors = self.validator.validate(manifest)
        if errors:
            await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error='; '.join(errors))
            self._logger.error("manifest_validation_failed", plugin_id=plugin_id, errors=errors)
            return False

        await self.registry.update_status(plugin_id, PluginStatus.VALIDATED)
        self._logger.info("manifest_validated", plugin_id=plugin_id)
        return True

    async def resolve_dependencies(self, plugin_id: str) -> bool:
        """Resolve dependencies using DependencyResolver with topological sort."""
        descriptor = await self.registry.get_descriptor(plugin_id)
        if not descriptor:
            raise ValueError(f"Plugin not found: {plugin_id}")

        manifest = descriptor.manifest
        deps = manifest.dependencies or []

        if not deps:
            self._logger.info("no_dependencies", plugin_id=plugin_id)
            return True

        # Use DependencyResolver for topological sort and circular detection
        try:
            resolved_order = await self.dependency_resolver.resolve(plugin_id)
            self._logger.info("dependencies_resolved", plugin_id=plugin_id, order=resolved_order)

            # Validate that all dependencies are ready
            valid = await self.dependency_resolver.validate_dependencies(plugin_id)
            if not valid:
                await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error="Dependencies not ready")
                return False

            return True
        except ValueError as e:
            await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=str(e))
            self._logger.error("dependency_resolution_failed", plugin_id=plugin_id, error=str(e))
            return False

    async def register(self, plugin_id: str) -> None:
        """Set plugin status to REGISTERED (idempotent).
        Note: registry.register() already called during install; this just updates status.
        """
        descriptor = await self.registry.get_descriptor(plugin_id)
        if not descriptor:
            raise ValueError(f"Plugin not found: {plugin_id}")
        await self.registry.update_status(plugin_id, PluginStatus.REGISTERED)

    async def enable(self, plugin_id: str) -> None:
        descriptor = await self.registry.get_descriptor(plugin_id)
        if not descriptor:
            raise ValueError(f"Plugin not found: {plugin_id}")
        await self.registry.update_status(plugin_id, PluginStatus.ENABLED)
        self._logger.info("plugin_enabled", plugin_id=plugin_id)

    async def initialize(self, plugin_id: str, context: Any) -> None:
        """Import plugin entrypoint and call initialize(context) if present."""
        descriptor = await self.registry.get_descriptor(plugin_id)
        if not descriptor:
            raise ValueError(f"Plugin not found: {plugin_id}")

        manifest = descriptor.manifest
        entry = manifest.entrypoint
        module_path, _, func_name = entry.rpartition('.')
        if not module_path:
            raise ValueError(f"Invalid entrypoint for plugin {plugin_id}: {entry}")

        try:
            module = importlib.import_module(module_path)
        except Exception as e:
            await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=f"ImportError: {e}")
            self._logger.error("initialize_import_failed", plugin_id=plugin_id, error=str(e))
            return

        init_fn = getattr(module, func_name, None)
        if init_fn is None:
            # maybe entrypoint referenced module; try module.initialize
            init_fn = getattr(module, 'initialize', None)

        if init_fn is None:
            # No initialize function; still mark as INITIALIZED
            await self.registry.update_status(plugin_id, PluginStatus.INITIALIZED)
            self._logger.info("no_initialize_fn", plugin_id=plugin_id)
            return

        try:
            if inspect.iscoroutinefunction(init_fn):
                await init_fn(context)
            else:
                # run sync function in threadpool
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: init_fn(context))

            await self.registry.update_status(plugin_id, PluginStatus.INITIALIZED)
            self._logger.info("plugin_initialized", plugin_id=plugin_id)
        except Exception as e:
            await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=f"InitializeError: {e}")
            self._logger.error("initialize_failed", plugin_id=plugin_id, error=str(e))

    async def health_check(self, plugin_id: str) -> None:
        descriptor = await self.registry.get_descriptor(plugin_id)
        if not descriptor:
            raise ValueError(f"Plugin not found: {plugin_id}")

        manifest = descriptor.manifest
        entry = manifest.entrypoint
        module_path, _, func_name = entry.rpartition('.')
        try:
            module = importlib.import_module(module_path)
        except Exception as e:
            await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=f"ImportError: {e}")
            self._logger.error("health_import_failed", plugin_id=plugin_id, error=str(e))
            return

        health_fn = getattr(module, 'health', None)
        if health_fn is None:
            # No health function - assume healthy
            await self.registry.update_status(plugin_id, PluginStatus.HEALTHY)
            return

        try:
            if inspect.iscoroutinefunction(health_fn):
                res = await health_fn()
            else:
                loop = asyncio.get_running_loop()
                res = await loop.run_in_executor(None, health_fn)

            # Expect res to be dict with status key
            if isinstance(res, dict) and res.get('status') == 'healthy':
                await self.registry.update_status(plugin_id, PluginStatus.HEALTHY)
                self._logger.info("plugin_healthy", plugin_id=plugin_id)
            else:
                await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=str(res))
                self._logger.warn("plugin_unhealthy", plugin_id=plugin_id, result=res)
        except Exception as e:
            await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=f"HealthError: {e}")
            self._logger.error("health_check_failed", plugin_id=plugin_id, error=str(e))

    async def disable(self, plugin_id: str) -> None:
        descriptor = await self.registry.get_descriptor(plugin_id)
        if not descriptor:
            raise ValueError(f"Plugin not found: {plugin_id}")
        await self.registry.update_status(plugin_id, PluginStatus.DISABLED)
        self._logger.info("plugin_disabled", plugin_id=plugin_id)

    async def unload(self, plugin_id: str) -> None:
        descriptor = await self.registry.get_descriptor(plugin_id)
        if not descriptor:
            raise ValueError(f"Plugin not found: {plugin_id}")

        manifest = descriptor.manifest
        entry = manifest.entrypoint
        module_path, _, func_name = entry.rpartition('.')
        try:
            module = importlib.import_module(module_path)
        except Exception as e:
            await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=f"ImportError: {e}")
            self._logger.error("unload_import_failed", plugin_id=plugin_id, error=str(e))
            return

        shutdown_fn = getattr(module, 'shutdown', None)
        if shutdown_fn is None:
            await self.registry.update_status(plugin_id, PluginStatus.UNLOADED)
            self._logger.info("no_shutdown_fn", plugin_id=plugin_id)
            return

        try:
            if inspect.iscoroutinefunction(shutdown_fn):
                await shutdown_fn()
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, shutdown_fn)

            await self.registry.update_status(plugin_id, PluginStatus.UNLOADED)
            self._logger.info("plugin_unloaded", plugin_id=plugin_id)
        except Exception as e:
            await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=f"UnloadError: {e}")
            self._logger.error("unload_failed", plugin_id=plugin_id, error=str(e))

    async def upgrade(
        self,
        plugin_id: str,
        new_manifest: PluginManifest,
        force: bool = False,
    ) -> str:
        """Upgrade a plugin to a new manifest version.

        Validates version upgrade compatibility:
        - New version must be strictly greater than old version.
        - Major version upgrade (1.x -> 2.x) requires --force flag.
        - New dependencies must be compatible with existing plugins.

        On failure, rollback to the old manifest and status.

        Args:
            plugin_id: Plugin identifier.
            new_manifest: New PluginManifest with updated version/data.
            force: If True, allow major version upgrades.

        Returns:
            plugin_id on success.

        Raises:
            ValueError: If validation fails or upgrade cannot proceed.
        """
        old_descriptor = await self.registry.get_descriptor(plugin_id)
        if not old_descriptor:
            raise ValueError(f"Plugin not found: {plugin_id}")

        old_manifest = old_descriptor.manifest
        old_status = old_descriptor.status
        old_error = old_descriptor.error

        # Validate new version > old version
        try:
            old_ver = Version(old_manifest.version)
            new_ver = Version(new_manifest.version)
        except Exception as e:
            raise ValueError(f"Invalid version format: {e}")

        if new_ver <= old_ver:
            raise ValueError(
                f"New version {new_manifest.version} must be greater than "
                f"old version {old_manifest.version}"
            )

        # Major version check
        if new_ver.major > old_ver.major and not force:
            raise ValueError(
                f"Major version upgrade ({old_manifest.version} -> "
                f"{new_manifest.version}) requires --force flag"
            )

        # Validate new manifest schema
        errors = self.validator.validate(new_manifest)
        if errors:
            raise ValueError(f"New manifest validation failed: {'; '.join(errors)}")

        # Perform upgrade with rollback on failure
        old_manifest_snapshot = old_manifest.model_copy()
        old_status_snapshot = old_status
        old_error_snapshot = old_error

        try:
            # 1. Unload old plugin
            try:
                await self.unload(plugin_id)
            except Exception as e:
                self._logger.warning("unload_during_upgrade_ignored", plugin_id=plugin_id, error=str(e))

            # 2. Replace manifest in registry (preserve plugin_id)
            new_manifest.id = plugin_id
            await self.registry.unregister(plugin_id)
            await self.registry.register(new_manifest)

            # 3. Restore lifecycle to previous active status (or ENABLED if it was healthy)
            if old_status_snapshot in (PluginStatus.HEALTHY, PluginStatus.ENABLED, PluginStatus.INITIALIZED):
                await self.registry.update_status(plugin_id, PluginStatus.ENABLED)

            self._logger.info(
                "plugin_upgraded",
                plugin_id=plugin_id,
                old_version=old_manifest.version,
                new_version=new_manifest.version,
            )

            return plugin_id

        except Exception as e:
            # ROLLBACK: restore old manifest
            self._logger.error(
                "upgrade_failed_rolling_back",
                plugin_id=plugin_id,
                error=str(e),
            )

            # Re-register old manifest
            try:
                await self.registry.unregister(plugin_id)
            except Exception:
                pass
            await self.registry.register(old_manifest_snapshot)
            await self.registry.update_status(plugin_id, old_status_snapshot, error=old_error_snapshot)

            self._logger.info(
                "upgrade_rolled_back",
                plugin_id=plugin_id,
                version=old_manifest_snapshot.version,
            )

            raise ValueError(f"Upgrade failed and rolled back: {e}")

    async def uninstall(self, plugin_id: str) -> None:
        # Best-effort: unload then remove from registry
        try:
            await self.unload(plugin_id)
        except Exception:
            self._logger.exception("unload_during_uninstall_failed", plugin_id=plugin_id)

        await self.registry.update_status(plugin_id, PluginStatus.UNINSTALLED)
        await self.registry.unregister(plugin_id)
        self._logger.info("plugin_uninstalled", plugin_id=plugin_id)