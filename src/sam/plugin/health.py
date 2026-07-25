"""
Plugin Health Checker for SAM Framework.

Provides health monitoring capabilities for plugins.
"""

import asyncio
import importlib
import inspect
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .models import PluginManifest, PluginStatus
from .registry import PluginRegistry, PluginDescriptor
import structlog


class PluginHealthStatus(BaseModel):
    """Health status of a plugin."""
    plugin_id: str
    status: str = Field(..., description="Health status: healthy, degraded, unhealthy, unknown")
    message: Optional[str] = None
    last_check: datetime = Field(default_factory=datetime.utcnow)
    capabilities: List[str] = Field(default_factory=list)
    version: str = ""


class PluginHealthChecker:
    """
    Health checker for plugins.

    Checks plugin health by calling plugin's health() function if available,
    otherwise falls back to registry status.
    """

    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._logger = structlog.get_logger()

    async def check(self, plugin_id: str) -> PluginHealthStatus:
        """
        Check health of a single plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            PluginHealthStatus with health information
        """
        descriptor = await self.registry.get_descriptor(plugin_id)
        if not descriptor:
            return PluginHealthStatus(
                plugin_id=plugin_id,
                status="unknown",
                message=f"Plugin not found in registry: {plugin_id}",
                last_check=datetime.utcnow()
            )

        manifest = descriptor.manifest
        entry = manifest.entrypoint
        module_path, _, func_name = entry.rpartition('.')

        # Try to import plugin module and call health() function
        health_fn = None
        try:
            module = importlib.import_module(module_path)
            health_fn = getattr(module, 'health', None)
        except Exception as e:
            self._logger.warning("health_import_failed", plugin_id=plugin_id, error=str(e))

        if health_fn is None:
            # No health function - fallback to registry status
            registry_status = descriptor.status.value if hasattr(descriptor.status, 'value') else str(descriptor.status)
            return PluginHealthStatus(
                plugin_id=plugin_id,
                status=registry_status,
                message=f"No health() function found, using registry status: {registry_status}",
                last_check=datetime.utcnow(),
                capabilities=manifest.capabilities,
                version=manifest.version
            )

        # Call health function
        try:
            if inspect.iscoroutinefunction(health_fn):
                result = await health_fn()
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, health_fn)

            # Parse result
            if isinstance(result, dict):
                status = result.get('status', 'healthy').lower()
                message = result.get('message')
            elif isinstance(result, str):
                status = result.lower()
                message = None
            elif isinstance(result, bool):
                status = 'healthy' if result else 'unhealthy'
                message = None
            else:
                status = 'healthy'
                message = str(result)

            # Normalize status
            if status not in ('healthy', 'degraded', 'unhealthy'):
                status = 'healthy'

            return PluginHealthStatus(
                plugin_id=plugin_id,
                status=status,
                message=message,
                last_check=datetime.utcnow(),
                capabilities=manifest.capabilities,
                version=manifest.version
            )

        except Exception as e:
            self._logger.error("health_check_failed", plugin_id=plugin_id, error=str(e))
            return PluginHealthStatus(
                plugin_id=plugin_id,
                status="unhealthy",
                message=f"Health check failed: {e}",
                last_check=datetime.utcnow(),
                capabilities=manifest.capabilities,
                version=manifest.version
            )

    async def check_all(self) -> Dict[str, PluginHealthStatus]:
        """
        Check health of all registered plugins.

        Returns:
            Dictionary mapping plugin_id to PluginHealthStatus
        """
        descriptors = await self.registry.list_descriptors()
        results = {}

        # Run checks concurrently
        tasks = []
        for descriptor in descriptors:
            plugin_id = descriptor.manifest.id or descriptor.manifest.name
            tasks.append(self.check(plugin_id))

        health_statuses = await asyncio.gather(*tasks, return_exceptions=True)

        for i, descriptor in enumerate(descriptors):
            plugin_id = descriptor.manifest.id or descriptor.manifest.name
            result = health_statuses[i]
            if isinstance(result, Exception):
                results[plugin_id] = PluginHealthStatus(
                    plugin_id=plugin_id,
                    status="unhealthy",
                    message=f"Health check raised exception: {result}",
                    last_check=datetime.utcnow(),
                    capabilities=descriptor.manifest.capabilities,
                    version=descriptor.manifest.version
                )
            else:
                results[plugin_id] = result

        return results

    async def periodic_check(
        self,
        interval: int = 60,
        stop_event: Optional[asyncio.Event] = None
    ) -> None:
        """
        Periodically check health of all plugins.

        Args:
            interval: Check interval in seconds (default: 60)
            stop_event: Optional event to signal stop
        """
        self._logger.info("periodic_health_check_started", interval=interval)

        while True:
            if stop_event and stop_event.is_set():
                self._logger.info("periodic_health_check_stopped")
                break

            try:
                await self.check_all()
            except Exception as e:
                self._logger.error("periodic_health_check_error", error=str(e))

            # Wait for interval or stop signal
            if stop_event:
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=interval)
                    if stop_event.is_set():
                        break
                except asyncio.TimeoutError:
                    continue
            else:
                await asyncio.sleep(interval)