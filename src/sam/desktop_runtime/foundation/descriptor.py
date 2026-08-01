"""Sprint 272 - Desktop Runtime Foundation: descriptor."""
from __future__ import annotations

from dataclasses import dataclass, field

from .metadata import DesktopMetadata


@dataclass(frozen=True)
class DesktopDescriptor:
    """Deskriptor immutable untuk subsistem Desktop Runtime."""

    name: str = "desktop_runtime"
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
    metadata: DesktopMetadata = field(default_factory=DesktopMetadata)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "kind": self.kind,
            "description": self.description,
            "layers": list(self.layers),
            "metadata": self.metadata.as_dict(),
        }
