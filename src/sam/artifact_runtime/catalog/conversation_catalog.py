"""Conversation Catalog Bridge — 5 read-only queries (Sprint 224)."""
from __future__ import annotations

from .artifact_catalog import ArtifactCatalog
from .artifact_loader import ArtifactLoader
from .artifact_history import ArtifactRecorder
from .artifact_index import ArtifactIndexer
from .artifact_version import ArtifactVersionProvider
from ..model.artifact import Artifact


class ConversationCatalogBridge:
    """Bridge conversation — 5 query catalog artifact."""

    def __init__(self) -> None:
        self._cat = ArtifactCatalog().add(Artifact("out", "report"))
        self._loader = ArtifactLoader()
        self._recorder = ArtifactRecorder()
        self._indexer = ArtifactIndexer()
        self._version = ArtifactVersionProvider()

    def query_1_count(self) -> int:
        return self._cat.count()

    def query_2_lookup(self, name: str) -> dict:
        a = self._cat.get(name)
        return {"found": a is not None}

    def query_3_loader(self) -> dict:
        res = self._loader.load((Artifact("a", "log"),))
        return {"loaded": res.loaded, "external_calls": res.external_calls}

    def query_4_history(self) -> dict:
        h = self._recorder.append("out")
        return {"count": h.count()}

    def query_5_version(self) -> dict:
        v = self._version.version()
        return {"version": v.version, "phase": v.phase}
