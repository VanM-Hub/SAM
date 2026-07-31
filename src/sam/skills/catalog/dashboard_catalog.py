"""Dashboard Catalog Bridge — 5 ExecutionCards (Sprint 168)."""
from __future__ import annotations

from .skill_catalog import SkillCatalog
from ..dashboard.skill_dashboard import ExecutionCard


class DashboardCatalogBridge:
    """Bridge dashboard — 5 kartu untuk skill catalog."""

    def __init__(self, catalog: SkillCatalog) -> None:
        self._catalog = catalog

    def cards(self):
        n = self._catalog.count()
        return [
            ExecutionCard("catalog.entries", "catalog", "ready",
                          f"{n} skill(s) in catalog", "skill catalog", "ready"),
            ExecutionCard("catalog.search", "catalog", "ready",
                          "search enabled", "read-only", "ready"),
            ExecutionCard("catalog.index", "catalog", "ready",
                          "tag index built", "skill index", "ready"),
            ExecutionCard("catalog.version", "catalog", "ready",
                          "version tracking", "skill version", "ready"),
            ExecutionCard("catalog.loader", "catalog", "ready",
                          "loader build-only", "skill loader", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
