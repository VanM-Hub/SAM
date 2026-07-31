"""Dashboard Catalog Bridge — 5 ExecutionCards (Sprint 176)."""
from __future__ import annotations

from .memory_catalog import MemoryCatalog
from ..dashboard.memory_dashboard import ExecutionCard


class DashboardCatalogBridge:
    """Bridge dashboard — 5 kartu untuk memory catalog."""

    def __init__(self, catalog: MemoryCatalog) -> None:
        self._catalog = catalog

    def cards(self):
        n = self._catalog.count()
        return [
            ExecutionCard("catalog.entries", "catalog", "ready",
                          f"{n} memory(s) in catalog", "memory catalog", "ready"),
            ExecutionCard("catalog.search", "catalog", "ready",
                          "search enabled", "read-only", "ready"),
            ExecutionCard("catalog.index", "catalog", "ready",
                          "tag index built", "memory index", "ready"),
            ExecutionCard("catalog.version", "catalog", "ready",
                          "version tracking", "memory version", "ready"),
            ExecutionCard("catalog.loader", "catalog", "ready",
                          "loader read-only", "memory loader", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
