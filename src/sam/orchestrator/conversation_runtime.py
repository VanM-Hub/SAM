# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 124 - Runtime Discovery: conversation_runtime.

Read-only conversation bridge for runtime discovery.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from .runtime_catalog import RuntimeCatalog
from .runtime_locator import RuntimeLocator
from .runtime_inventory import RuntimeInventory, RuntimeInventoryBuilder
from .runtime_descriptor import RuntimeDescriptor


class ConversationRuntimeBridge:
    """Read-only bridge exposing discovered runtimes."""

    def __init__(self, catalog: RuntimeCatalog) -> None:
        self._catalog = catalog
        self._locator = RuntimeLocator(catalog)
        self._inventory = RuntimeInventoryBuilder(catalog)

    def count(self) -> int:
        return self._catalog.count()

    def locate(self, runtime_id: str) -> Optional[RuntimeDescriptor]:
        return self._locator.by_id(runtime_id)

    def inventory(self) -> RuntimeInventory:
        return self._inventory.build()

    def list_names(self) -> Tuple[str, ...]:
        return tuple(d.name for d in self._catalog.all())

    def summary(self) -> Dict[str, int]:
        return {"runtimes": self._catalog.count()}
