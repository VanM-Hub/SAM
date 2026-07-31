# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 124 - Runtime Discovery: runtime_catalog.

Catalog of discovered runtime descriptors. Pure in-memory, sync.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple, FrozenSet

from .runtime_descriptor import RuntimeDescriptor


class RuntimeCatalog:
    """Catalog that records discovered runtimes."""

    def __init__(self) -> None:
        self._items: Dict[str, RuntimeDescriptor] = {}

    def add(self, descriptor: RuntimeDescriptor) -> None:
        self._items[descriptor.runtime_id] = descriptor

    def get(self, runtime_id: str) -> Optional[RuntimeDescriptor]:
        return self._items.get(runtime_id)

    def all(self) -> Tuple[RuntimeDescriptor, ...]:
        return tuple(
            sorted(self._items.values(), key=lambda d: d.pipeline_position)
        )

    def ids(self) -> FrozenSet[str]:
        return frozenset(self._items.keys())

    def count(self) -> int:
        return len(self._items)
