"""Sprint 274 - Desktop Panels: panel model (immutable)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PanelModel:
    """Model panel deklaratif (tanpa state mutabel, tanpa eksekusi)."""

    name: str
    kind: str = "panel"
    title: str = ""
    source_runtime: str = ""
    readonly: bool = True

    def __post_init__(self):
        if not self.title:
            object.__setattr__(self, "title", self.name)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "title": self.title,
            "source_runtime": self.source_runtime,
            "readonly": self.readonly,
        }
