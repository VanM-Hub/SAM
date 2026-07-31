"""Dashboard Catalog Bridge — 5 PolicyCards (Sprint 224)."""
from __future__ import annotations

from ..dashboard import PolicyCard


class DashboardCatalogBridge:
    """Bridge dashboard — 5 kartu catalog artifact."""

    def cards(self):
        return [
            PolicyCard("ac.catalog", "artifact", "ready",
                       "ArtifactCatalog read-only", "catalog", "ready"),
            PolicyCard("ac.index", "artifact", "ready",
                       "ArtifactIndex immutable", "catalog", "ready"),
            PolicyCard("ac.loader", "artifact", "ready",
                       "no file read / no cache", "catalog", "ready"),
            PolicyCard("ac.version", "artifact", "ready",
                       "version deterministic", "catalog", "ready"),
            PolicyCard("ac.history", "artifact", "ready",
                       "in-memory no disk write", "catalog", "ready"),
        ]
