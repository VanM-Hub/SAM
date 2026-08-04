"""Artifact Preview Consumer (Session 07 - Artifact Runtime Activation).

AD-ENG-002 Activation Pattern Standard:
  Conversation -> RuntimeService -> ExecutionRuntime(preview)
  -> ArtifactPreviewConsumer -> ArtifactRegistry -> ConversationArtifactBridge -> STOP.

Wire Artifact di entry via jalur resmi, pakai ArtifactRegistry +
ConversationArtifactBridge + ConversationIntegrationBridge yang SUDAH ADA.
Tanpa ArtifactEngine/Generator/Runtime baru; tanpa ubah ExecutionRuntime/RuntimeService/
internal artifact_runtime; tanpa integrasi Mission/Contract/Dashboard/Intelligence.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.artifact_runtime.foundation.artifact_registry import ArtifactRegistry
from sam.artifact_runtime.foundation.conversation_artifact import (
    ConversationArtifactBridge,
)
from sam.artifact_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)


@dataclass(frozen=True)
class ArtifactPreview:
    """Snapshot artifact (immutable, read-only). Preview-only, no generate/storage."""
    artifact_name: str
    found: bool = False
    category: str = ""
    version: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    integration_ok: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "artifact_name": self.artifact_name,
            "found": self.found,
            "category": self.category,
            "version": self.version,
            "metadata": dict(self.metadata),
            "integration_ok": self.integration_ok,
            "external_calls": self.external_calls,
        }


class ArtifactPreviewConsumer:
    """Consumer Artifact via jalur Conversation -> RuntimeService.

    Membaca artifact dari registry (yang sudah ada), resolve via bridge.
    BUKAN pipeline internal; tidak mengubah ExecutionRuntime/RuntimeService.
    Tidak menghubungkan Mission/Contract/Dashboard/Intelligence.
    """

    def __init__(self, registry: Optional[ArtifactRegistry] = None) -> None:
        self._registry = registry or ArtifactRegistry()
        self._bridge = ConversationArtifactBridge(self._registry)
        self._integ = ConversationIntegrationBridge(self._registry)

    @property
    def registry(self) -> ArtifactRegistry:
        return self._registry

    def list_artifacts(self) -> List[str]:
        """Daftar nama artifact (read-only)."""
        return list(self._registry.names())

    def resolve_artifact(self, artifact_name: str) -> ArtifactPreview:
        """Resolve satu artifact via bridge (read-only, no generate/storage)."""
        descriptor = self._registry.lookup(artifact_name)
        if descriptor is None:
            return ArtifactPreview(artifact_name=artifact_name, found=False)
        run = self._integ.query_3_pipeline(artifact_name)
        return ArtifactPreview(
            artifact_name=artifact_name,
            found=True,
            category=descriptor.category,
            version=descriptor.version,
            metadata=self._bridge.query_5_metadata(),
            integration_ok=bool(run.get("ok")),
            external_calls=0,
        )

    def summary(self) -> dict:
        """Ringkasan artifact registry (read-only)."""
        return {
            "total_artifact": self._registry.count(),
            "names": list(self._registry.names()),
        }
