"""Dashboard Catalog Bridge — 5 ExecutionCards (Sprint 184)."""
from __future__ import annotations

from .knowledge_catalog import KnowledgeCatalog
from ..dashboard.knowledge_dashboard import ExecutionCard


class DashboardCatalogBridge:
    """Bridge dashboard — 5 kartu untuk knowledge catalog."""

    def __init__(self, catalog: KnowledgeCatalog) -> None:
        self._catalog = catalog

    def cards(self):
        n = self._catalog.count()
        return [
            ExecutionCard("catalog.entries", "catalog", "ready",
                          f"{n} knowledge(s) in catalog", "knowledge catalog", "ready"),
            ExecutionCard("catalog.search", "catalog", "ready",
                          "search enabled", "read-only", "ready"),
            ExecutionCard("catalog.index", "catalog", "ready",
                          "tag index built", "knowledge index", "ready"),
            ExecutionCard("catalog.version", "catalog", "ready",
                          "version tracking", "knowledge version", "ready"),
            ExecutionCard("catalog.loader", "catalog", "ready",
                          "loader read-only", "knowledge loader", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
