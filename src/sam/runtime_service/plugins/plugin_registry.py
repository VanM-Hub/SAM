"""PluginRegistry (Sprint 266).

Program D - Runtime Services & Deployment.
Registry plugin (deterministic, read-only).
"""
from __future__ import annotations
from typing import Dict, List, Optional

from .plugin_descriptor import PluginDescriptor


class PluginRegistry:
    """Registry plugin (sync, deterministic)."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginDescriptor] = {}

    def register(self, descriptor: PluginDescriptor) -> None:
        if descriptor.name in self._plugins:
            raise ValueError(f"plugin already registered: {descriptor.name}")
        self._plugins[descriptor.name] = descriptor

    def get(self, name: str) -> Optional[PluginDescriptor]:
        return self._plugins.get(name)

    def has(self, name: str) -> bool:
        return name in self._plugins

    def list(self) -> List[PluginDescriptor]:
        return [self._plugins[k] for k in sorted(self._plugins)]

    def names(self) -> List[str]:
        return sorted(self._plugins.keys())

    def count(self) -> int:
        return len(self._plugins)
