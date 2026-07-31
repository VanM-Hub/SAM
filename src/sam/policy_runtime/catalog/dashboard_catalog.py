"""Dashboard Catalog Bridge — 5 PolicyCards (Sprint 208)."""
from __future__ import annotations

from ..dashboard import PolicyCard
from ..model.policy import Policy
from .policy_catalog import PolicyCatalog
from .policy_loader import PolicyLoader


class DashboardCatalogBridge:
    """Bridge dashboard — 5 kartu untuk catalog policy."""

    def __init__(self, catalog: PolicyCatalog = None) -> None:
        self._catalog = catalog or PolicyCatalog()
        self._loader = PolicyLoader(self._catalog)

    def cards(self, policy: Policy = None):
        pol = policy or Policy("pol0")
        return [
            PolicyCard("ct.policy", "catalog", "ready",
                       f"{pol.policy_id} ({pol.rule_count()} rules)",
                       "policy", "ready"),
            PolicyCard("ct.catalog", "catalog", "ready",
                       f"{self._catalog.count()} policy(s) catalogued",
                       "catalog", "ready"),
            PolicyCard("ct.index", "catalog", "ready",
                       "PolicyIndex frozen (tuple rule ids)", "index", "ready"),
            PolicyCard("ct.no_read", "catalog", "ready",
                       "catalog: read-only, no file, no cache", "preview", "ready"),
            PolicyCard("ct.version", "catalog", "ready",
                       "PolicyVersionProvider 21.0.0", "version", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
