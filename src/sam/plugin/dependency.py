"""
Plugin Dependency Resolution – topological sort, validation, circular detection.

Manages plugin dependencies and provides resolution order for initialization.
"""

from typing import List, Set, Dict, Optional, Union
from collections import deque
import structlog

from .models import PluginManifest, PluginStatus
from .registry import PluginRegistry, PluginDescriptor
from .version import satisfies_all, VersionConstraintError


class DependencyResolver:
    """
    Resolves plugin dependencies with topological sort and circular detection.
    """

    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._logger = structlog.get_logger()

    async def resolve(self, plugin_id: str) -> List[str]:
        """
        Resolve dependencies for a plugin, returning topological order including the plugin.

        Args:
            plugin_id: Plugin ID to resolve dependencies for

        Returns:
            List of plugin IDs in dependency order (dependencies first, plugin last)

        Raises:
            ValueError: If circular dependency detected or missing dependency
        """
        manifest = await self.registry.get(plugin_id)
        if not manifest:
            raise ValueError(f"Plugin not found: {plugin_id}")

        # Get all dependent plugin IDs (excluding the target for collection)
        dep_ids = await self._collect_dependencies(plugin_id, set())
        # If there are no dependencies, return the plugin itself
        if not dep_ids:
            return [plugin_id]

        # Include the target for full topological sorting
        all_ids = set(dep_ids)
        all_ids.add(plugin_id)

        # Before sorting, validate version constraints across the subgraph
        for pid in list(all_ids):
            manifest = await self.registry.get(pid)
            if not manifest:
                continue
            for dep_entry in manifest.dependencies:
                # extract dep_id and constraint
                dep_id = None
                constraint = None
                if isinstance(dep_entry, dict):
                    dep_id = dep_entry.get("id")
                    constraint = dep_entry.get("version") or dep_entry.get("constraint")
                else:
                    if isinstance(dep_entry, str) and "@" in dep_entry:
                        dep_id, constraint = dep_entry.split("@", 1)
                    else:
                        dep_id = str(dep_entry)

                if dep_id not in all_ids:
                    continue

                if constraint:
                    dep_manifest = await self.registry.get(dep_id)
                    dep_version = getattr(dep_manifest, "version", None) if dep_manifest else None
                    try:
                        ok = satisfies_all(dep_version or "", constraint)
                    except VersionConstraintError as e:
                        self._logger.error(
                            "invalid_version_constraint",
                            target=plugin_id,
                            dependency=dep_id,
                            constraint=constraint,
                            error=str(e),
                        )
                        # mark original target degraded
                        await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=str(e))
                        raise ValueError(str(e))

                    if not ok:
                        msg = f"Dependency {dep_id} version {dep_version} does not satisfy constraint {constraint}"
                        self._logger.error(
                            "dependency_version_mismatch",
                            target=plugin_id,
                            dependency=dep_id,
                            required=constraint,
                            actual=dep_version,
                        )
                        await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=msg)
                        raise ValueError(msg)

        ordered = await self._topological_sort(all_ids, plugin_id)
        # _topological_sort returns dependencies (excluding target); append target at the end
        if plugin_id not in ordered:
            ordered.append(plugin_id)
        return ordered

    async def validate_dependencies(self, plugin_id: str) -> bool:
        """
        Validate that all dependencies are registered, enabled, and satisfy version constraints.

        Supports dependency entries in manifest as either:
          - simple strings: "plugin-id" or "plugin-id@>=1.0.0"
          - dicts: {"id": "plugin-id", "version": ">=1.0.0"}

        On missing dependency or version mismatch the plugin is marked DEGRADED.
        """
        manifest = await self.registry.get(plugin_id)
        if not manifest:
            self._logger.error("plugin_not_found", plugin_id=plugin_id)
            return False

        for dep_entry in manifest.dependencies:
            # support dict form {id: ..., version: ...} or string form 'id' or 'id@constraint'
            dep_id = None
            constraint = None
            if isinstance(dep_entry, dict):
                dep_id = dep_entry.get("id")
                constraint = dep_entry.get("version") or dep_entry.get("constraint")
            else:
                # string form
                if isinstance(dep_entry, str) and "@" in dep_entry:
                    dep_id, constraint = dep_entry.split("@", 1)
                else:
                    dep_id = str(dep_entry)

            desc = await self.registry.get_descriptor(dep_id)
            if not desc:
                self._logger.error(
                    "dependency_not_found",
                    plugin_id=plugin_id,
                    dependency=dep_id
                )
                # mark plugin degraded
                await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=f"Missing dependency {dep_id}")
                return False

            if desc.status.value not in ["enabled", "initialized", "healthy"]:
                self._logger.warning(
                    "dependency_not_ready",
                    plugin_id=plugin_id,
                    dependency=dep_id,
                    status=desc.status
                )
                return False

            # check version constraint if present
            if constraint:
                # fetch dependency manifest to get version
                dep_manifest = await self.registry.get(dep_id)
                dep_version = getattr(dep_manifest, "version", None) if dep_manifest else None
                try:
                    ok = satisfies_all(dep_version or "", constraint)
                except VersionConstraintError as e:
                    self._logger.error(
                        "invalid_version_constraint",
                        plugin_id=plugin_id,
                        dependency=dep_id,
                        constraint=constraint,
                        error=str(e)
                    )
                    await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=str(e))
                    return False

                if not ok:
                    msg = f"Dependency {dep_id} version {dep_version} does not satisfy constraint {constraint}"
                    self._logger.error(
                        "dependency_version_mismatch",
                        plugin_id=plugin_id,
                        dependency=dep_id,
                        required=constraint,
                        actual=dep_version,
                    )
                    # mark plugin degraded
                    await self.registry.update_status(plugin_id, PluginStatus.DEGRADED, error=msg)
                    return False

        return True

    async def get_resolution_order(self, plugin_ids: List[str]) -> List[str]:
        """
        Get resolution order for multiple plugins.

        Args:
            plugin_ids: List of plugin IDs to resolve

        Returns:
            List of plugin IDs in dependency order
        """
        all_plugins = set(plugin_ids)
        result = []

        for pid in plugin_ids:
            order = await self.resolve(pid)
            for dep in order:
                if dep not in result and dep in all_plugins:
                    result.append(dep)

        # Add plugins that weren't in any dependency chain
        for pid in plugin_ids:
            if pid not in result:
                result.append(pid)

        return result

    async def _collect_dependencies(self, plugin_id: str, visited: Set[str]) -> Set[str]:
        """
        Recursively collect all dependencies (DFS).

        Returns:
            Set of all dependency plugin IDs
        """
        if plugin_id in visited:
            return set()

        visited.add(plugin_id)
        manifest = await self.registry.get(plugin_id)
        if not manifest:
            return set()

        deps = set()
        for dep_entry in manifest.dependencies:
            # Extract dependency ID from dict or string@constraint format
            dep_id = None
            if isinstance(dep_entry, dict):
                dep_id = dep_entry.get("id")
            elif isinstance(dep_entry, str) and "@" in dep_entry:
                dep_id = dep_entry.split("@", 1)[0]
            else:
                dep_id = str(dep_entry)
            
            if dep_id:
                deps.add(dep_id)
                sub_deps = await self._collect_dependencies(dep_id, visited)
                deps.update(sub_deps)

        return deps

    async def _topological_sort(self, plugin_ids: Set[str], target: str) -> List[str]:
        """
        Topological sort with circular detection.

        Args:
            plugin_ids: Set of plugin IDs to sort (including target)
            target: Target plugin ID (for error messages)

        Returns:
            List of plugin IDs in topological order (dependencies first)

        Raises:
            ValueError: If circular dependency detected
        """
        # Build reverse graph: dependency -> dependents
        # If A depends on B, edge B -> A (B must come before A)
        graph: Dict[str, Set[str]] = {pid: set() for pid in plugin_ids}
        in_degree: Dict[str, int] = {pid: 0 for pid in plugin_ids}

        for pid in plugin_ids:
            manifest = await self.registry.get(pid)
            if not manifest:
                continue
            for dep_entry in manifest.dependencies:
                # Extract dependency ID
                dep_id = None
                if isinstance(dep_entry, dict):
                    dep_id = dep_entry.get("id")
                elif isinstance(dep_entry, str) and "@" in dep_entry:
                    dep_id = dep_entry.split("@", 1)[0]
                else:
                    dep_id = str(dep_entry)

                if dep_id in plugin_ids:
                    # dep must come before pid
                    graph[dep_id].add(pid)
                    in_degree[pid] += 1

        # Kahn's algorithm
        queue = deque([pid for pid, deg in in_degree.items() if deg == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(in_degree):
            # Circular dependency detected
            remaining = set(in_degree.keys()) - set(result)
            self._logger.error(
                "circular_dependency_detected",
                target=target,
                remaining=list(remaining),
                graph={k: list(v) for k, v in graph.items()}
            )
            raise ValueError(
                f"Circular dependency detected for plugin {target}: remaining nodes {remaining}"
            )

        # Remove target from result (we only need dependencies)
        if target in result:
            result.remove(target)

        return result