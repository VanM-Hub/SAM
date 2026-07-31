"""PluginRuntime (Sprint 266).

Program D - Runtime Services & Deployment.
Orkestrasi plugin runtime. Plugin hanya metadata.
"""
from __future__ import annotations
from typing import List, Optional

from .plugin_descriptor import PluginDescriptor
from .plugin_loader import PluginLoader
from .plugin_registry import PluginRegistry
from .plugin_validator import PluginValidator
from . import PLUGIN_NAMES


class PluginRuntime:
    """Runtime plugin (sync, deterministic). Metadata only."""

    def __init__(self) -> None:
        self._registry = PluginRegistry()
        self._loader = PluginLoader(self._registry)
        self._validator = PluginValidator()
        self._load_defaults()

    def _load_defaults(self) -> None:
        defaults = {
            "openai": PluginDescriptor(name="openai", secret_key="OPENAI_API_KEY",
                                       capabilities=["chat", "embedding", "vision"]),
            "anthropic": PluginDescriptor(name="anthropic", secret_key="ANTHROPIC_API_KEY",
                                          capabilities=["chat", "vision"]),
            "gemini": PluginDescriptor(name="gemini", secret_key="GEMINI_API_KEY",
                                       capabilities=["chat", "embedding", "vision"]),
            "deepseek": PluginDescriptor(name="deepseek", secret_key="DEEPSEEK_API_KEY",
                                         capabilities=["chat", "reasoning"]),
            "openrouter": PluginDescriptor(name="openrouter", secret_key="OPENROUTER_API_KEY",
                                           capabilities=["chat", "routing"]),
            "ollama": PluginDescriptor(name="ollama", kind="provider",
                                       capabilities=["chat", "embedding"]),
            "openclaw": PluginDescriptor(name="openclaw", kind="integration",
                                         secret_key="OPENCLAW_URL",
                                         capabilities=["gateway", "tools"]),
        }
        for name in PLUGIN_NAMES:
            d = defaults[name]
            if self._validator.is_valid(d):
                self._registry.register(d)

    def get(self, name: str) -> Optional[PluginDescriptor]:
        return self._registry.get(name)

    def list(self) -> List[PluginDescriptor]:
        return self._registry.list()

    def names(self) -> List[str]:
        return self._registry.names()

    def count(self) -> int:
        return self._registry.count()
