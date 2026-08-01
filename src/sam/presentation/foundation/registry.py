"""Sprint 272 - Presentation Layer Foundation: registry (metadata-only)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .descriptor import PresentationDescriptor


@dataclass(frozen=True)
class RegistryEntry:
    """Entri registri : nama komponen + tipe (metadata-only)."""

    name: str
    kind: str


@dataclass(frozen=True)
class PresentationRegistry:
    """Registri komponen yang dikenal Presentation Layer.

    Daftar bersifat struktural/deskriptif. Default kosong; komponen
    ditambahkan lewat builder/register (tanpa hardcode).
    """

    descriptor: PresentationDescriptor = field(default_factory=PresentationDescriptor)
    _entries: Tuple[RegistryEntry, ...] = ()

    def with_entry(self, name: str, kind: str) -> "PresentationRegistry":
        return PresentationRegistry(
            descriptor=self.descriptor,
            _entries=self._entries + (RegistryEntry(name=name, kind=kind),),
        )

    @property
    def entries(self) -> Tuple[RegistryEntry, ...]:
        return self._entries

    @property
    def names(self) -> Tuple[str, ...]:
        return tuple(e.name for e in self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def as_dict(self) -> dict:
        return {
            "descriptor": self.descriptor.as_dict(),
            "entries": [e.name for e in self._entries],
        }


KNOWN_COMPONENTS: Tuple[str, ...] = (
    "Workspace",
    "Panels",
    "Dashboard",
    "Runtime",
    "Monitoring",
    "Certification",
    "Integration",
)
