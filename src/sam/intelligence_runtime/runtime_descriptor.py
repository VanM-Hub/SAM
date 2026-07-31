"""Sprint 262 - Runtime Registry: runtime_descriptor."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeDescriptor:
    """Deskripsi immutable sebuah runtime yang terdaftar."""

    name: str
    kind: str
    version: str = "28.0.0"

    def as_dict(self) -> dict:
        return {"name": self.name, "kind": self.kind, "version": self.version}
