"""
OP-368 — Plugin Discovery
==========================

Read-only plugin folder scanner.
Does NOT load or execute any plugin code.
"""

from sam.launcher.version import PluginDiscovery, PluginInfo  # noqa: F401

__all__ = ["PluginDiscovery", "PluginInfo"]
