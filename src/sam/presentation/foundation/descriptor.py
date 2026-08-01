"""Sprint 272 - Presentation Layer Foundation: descriptor."""
from __future__ import annotations

from dataclasses import dataclass, field

from .metadata import PresentationMetadata


@dataclass(frozen=True)
class PresentationDescriptor:
    """Deskriptor immutable untuk subsistem Presentation Layer."""

    name: str = "presentation"
    version: str = "29.0.0"
    kind: str = "desktop"
    description: str = (
        "UI resmi SAM - composition layer yang menghubungkan seluruh subsystem. "
        "Hanya visualisasi, tanpa business logic baru, tanpa eksekusi sendiri."
    )
    layers: tuple = (
        "foundation",
        "workspace",
        "panels",
        "dashboard",
        "runtime",
        "monitoring",
        "certification",
        "integration",
    )
    metadata: PresentationMetadata = field(default_factory=PresentationMetadata)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "kind": self.kind,
            "description": self.description,
            "layers": list(self.layers),
            "metadata": self.metadata.as_dict(),
        }
