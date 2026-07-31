# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 124 - Runtime Discovery: runtime_locator.

Locates runtimes within a catalog. Sync, deterministic, read-only.
"""
from __future__ import annotations

from typing import Optional, Tuple

from .runtime_catalog import RuntimeCatalog
from .runtime_descriptor import RuntimeDescriptor


class RuntimeLocator:
    """Finds runtimes by id, position, or tag."""

    def __init__(self, catalog: RuntimeCatalog) -> None:
        self._catalog = catalog

    def by_id(self, runtime_id: str) -> Optional[RuntimeDescriptor]:
        return self._catalog.get(runtime_id)

    def by_position(self, position: int) -> Tuple[RuntimeDescriptor, ...]:
        return tuple(d for d in self._catalog.all() if d.pipeline_position == position)

    def by_tag(self, tag: str) -> Tuple[RuntimeDescriptor, ...]:
        return tuple(d for d in self._catalog.all() if tag in d.tags)

    def all_ordered(self) -> Tuple[RuntimeDescriptor, ...]:
        return self._catalog.all()
