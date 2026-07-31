"""PluginLoader (Sprint 266).

Program D - Runtime Services & Deployment.
Memuat plugin dari definisi metadata. Tidak memanggil provider.
"""
from __future__ import annotations
from typing import Dict, List

from .plugin_descriptor import PluginDescriptor
from .plugin_registry import PluginRegistry


class PluginLoader:
    """Loader plugin dari metadata (sync, deterministic)."""

    def __init__(self, registry: PluginRegistry = None) -> None:
        self._registry = registry or PluginRegistry()

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    def load(self, descriptors: List[PluginDescriptor]) -> int:
        for d in descriptors:
            self._registry.register(d)
        return len(descriptors)

    def load_from_dicts(self, items: List[Dict]) -> int:
        loaded = 0
        for item in items:
            d = PluginDescriptor(**item)
            self._registry.register(d)
            loaded += 1
        return loaded
