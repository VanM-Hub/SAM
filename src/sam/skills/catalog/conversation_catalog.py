"""Conversation Catalog Bridge — query read-only (Sprint 168)."""
from __future__ import annotations

from .skill_catalog import SkillCatalog
from .skill_version import SkillVersionProvider


class ConversationCatalogBridge:
    """Bridge conversation — ringkasan katalog read-only."""

    def __init__(self, catalog: SkillCatalog, version: SkillVersionProvider = None) -> None:
        self._catalog = catalog
        self._version = version

    def summary(self) -> dict:
        return {"total": self._catalog.count()}

    def search(self, query: str) -> list:
        return [e.skill_id for e in self._catalog.search(query).entries]

    def version(self, skill_id: str) -> str:
        if self._version is None:
            return ""
        return self._version.version_of(skill_id)
