"""Runtime Catalog — katalog subsystem."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_registry import CatalogEntry


class RuntimeCatalog:
    """Katalog subsystem — preview-only."""

    def __init__(self) -> None:
        self._entries: Dict[str, CatalogEntry] = {}

    def register(self, entry: CatalogEntry) -> None:
        self._entries[entry.catalog_id] = entry

    def get(self, catalog_id: str) -> CatalogEntry | None:
        return self._entries.get(catalog_id)

    def list_by_category(self, category: str) -> List[CatalogEntry]:
        return [e for e in self._entries.values() if e.category == category]

    def count_entries(self) -> int:
        return len(self._entries)

    def list_all(self) -> List[CatalogEntry]:
        return list(self._entries.values())
