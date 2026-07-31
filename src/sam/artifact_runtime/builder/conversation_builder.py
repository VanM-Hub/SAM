"""Conversation Builder Bridge — 5 read-only queries (Sprint 222)."""
from __future__ import annotations

from .artifact_builder import ArtifactBuilder, ArtifactPreviewDTO
from .manifest_builder import ManifestBuilder
from .reference_builder import ReferenceBuilder
from .metadata_builder import MetadataBuilder


class ConversationBuilderBridge:
    """Bridge conversation — 5 query builder artifact."""

    def __init__(self) -> None:
        self._artifact = ArtifactBuilder()
        self._manifest = ManifestBuilder()
        self._ref = ReferenceBuilder()
        self._meta = MetadataBuilder()

    def query_1_build(self, name: str) -> dict:
        res = self._artifact.build(name, "report")
        return {"ok": res.ok, "artifact": res.artifact.name if res.artifact else None}

    def query_2_manifest(self) -> dict:
        m = self._manifest.build("mf", ("a", "b"))
        return {"name": m.name, "artifacts": list(m.artifacts)}

    def query_3_reference(self) -> dict:
        r = self._ref.build("ref1")
        return {"name": r.name, "traceable": r.traceable}

    def query_4_metadata(self) -> dict:
        m = self._meta.build("meta1")
        return {"name": m.name, "version": m.version}

    def query_5_preview(self, name: str) -> ArtifactPreviewDTO:
        return PreviewBuilderProxy().preview(name)


class PreviewBuilderProxy:
    def __init__(self) -> None:
        from .preview_builder import PreviewBuilder
        self._b = PreviewBuilder()

    def preview(self, name: str):
        return self._b.preview(name)
