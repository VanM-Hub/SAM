# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 124 - Runtime Discovery: runtime_inventory.

Builds the complete inventory of known runtimes from a catalog.
Produces a snapshot of what is available for orchestration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .runtime_catalog import RuntimeCatalog
from .runtime_descriptor import RuntimeDescriptor


@dataclass(frozen=True)
class RuntimeInventory:
    """Immutable inventory of available runtimes."""

    runtimes: Tuple[RuntimeDescriptor, ...]

    @property
    def count(self) -> int:
        return len(self.runtimes)

    @property
    def ids(self) -> Tuple[str, ...]:
        return tuple(d.runtime_id for d in self.runtimes)


class RuntimeInventoryBuilder:
    """Builds an available runtime inventory from the catalog."""

    def __init__(self, catalog: RuntimeCatalog) -> None:
        self._catalog = catalog

    def build(self) -> RuntimeInventory:
        return RuntimeInventory(runtimes=self._catalog.all())
