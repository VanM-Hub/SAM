"""Conversation Catalog Bridge — 5 query read-only (Sprint 208)."""
from __future__ import annotations

from ..model.policy import Policy
from .policy_catalog import PolicyCatalog
from .policy_loader import PolicyLoader
from .policy_index import PolicyIndexer
from .policy_version import PolicyVersionProvider
from .policy_history import PolicyHistory, PolicyHistoryEntry


class ConversationCatalogBridge:
    """Bridge conversation — 5 query read-only catalog policy."""

    def __init__(self, catalog: PolicyCatalog = None) -> None:
        self._catalog = catalog or PolicyCatalog()
        self._loader = PolicyLoader(self._catalog)
        self._indexer = PolicyIndexer()
        self._version = PolicyVersionProvider()
        self._history = PolicyHistory()

    def query_1_add(self, policy: Policy) -> dict:
        self._catalog.add(policy)
        self._history.record(PolicyHistoryEntry(
            policy_id=policy.policy_id, action="created",
        ))
        return {"added": policy.policy_id, "count": self._catalog.count()}

    def query_2_load(self, policy_id: str) -> dict:
        r = self._loader.load(policy_id)
        return {"ok": r.ok, "detail": r.detail}

    def query_3_search(self, policy_id: str, term: str) -> list:
        pol = self._catalog.get(policy_id)
        if pol is None:
            return []
        return self._indexer.search(
            self._indexer.index(pol, []), term,
        )

    def query_4_version(self, policy_id: str) -> dict:
        v = self._version.provide(policy_id)
        return {"version": v.version, "policy_id": v.policy_id}

    def query_5_history(self, policy_id: str) -> list:
        return [e.policy_id for e in self._history.by_policy(policy_id)]
