"""Sprint 261 - Intelligence Runtime Foundation: descriptor."""
from __future__ import annotations

from dataclasses import dataclass, field

from .metadata import IntelligenceMetadata


@dataclass(frozen=True)
class IntelligenceDescriptor:
    """Deskriptor immutable untuk subsistem Intelligence Runtime."""

    name: str = "intelligence_runtime"
    version: str = "28.0.0"
    kind: str = "unified_intelligence"
    description: str = (
        "Menyatukan representasi seluruh runtime SAM menjadi graph + context "
        "yang deterministik (preview-only, tanpa inference/LLM)."
    )
    layers: tuple = ("registry", "graph", "context", "validation", "assembly", "report")
    metadata: IntelligenceMetadata = field(default_factory=IntelligenceMetadata)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "kind": self.kind,
            "description": self.description,
            "layers": list(self.layers),
            "metadata": self.metadata.as_dict(),
        }
