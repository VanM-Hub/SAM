"""Dashboard Catalog Bridge — 5 PolicyCards (Sprint 216)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from .audit_catalog import AuditCatalog


class DashboardCatalogBridge:
    """Bridge dashboard — 5 kartu katalog audit."""

    def __init__(self, catalog: AuditCatalog) -> None:
        self._catalog = catalog

    def cards(self):
        n = self._catalog.count()
        return [
            PolicyCard("ac.catalog", "audit", "ready",
                          f"{n} audit(s) catalogued",
                          "catalog", "ready"),
            PolicyCard("ac.readonly", "audit", "ready",
                          "read-only catalog (no file, no cache)",
                          "catalog", "ready"),
            PolicyCard("ac.index", "audit", "ready",
                          "index of audit record ids",
                          "catalog", "ready"),
            PolicyCard("ac.history", "audit", "ready",
                          "in-memory history (no disk write)",
                          "catalog", "ready"),
            PolicyCard("ac.immutable", "audit", "immutable",
                          "immutable catalog & index",
                          "catalog", "immutable"),
        ]

    def verdict_card(self):
        return self.cards()[1]
