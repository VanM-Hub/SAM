"""Sprint 261 - Intelligence Runtime Foundation: registry (metadata-only, tanpa hardcode provider)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .descriptor import IntelligenceDescriptor


@dataclass(frozen=True)
class RegistryEntry:
    """Entri registri : nama runtime + tipe (metadata-only)."""

    name: str
    kind: str


@dataclass(frozen=True)
class IntelligenceRegistry:
    """Registri runtime yang dikenal Intelligence Runtime.

    Daftar ini bersifat struktural/deskriptif, BUKAN daftar provider API.
    Default kosong; runtime ditambahkan lewat builder/register (tanpa hardcode).
    """

    descriptor: IntelligenceDescriptor = field(
        default_factory=IntelligenceDescriptor
    )
    _entries: Tuple[RegistryEntry, ...] = ()

    def with_entry(self, name: str, kind: str) -> "IntelligenceRegistry":
        return IntelligenceRegistry(
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


KNOWN_RUNTIMES: Tuple[str, ...] = (
    "Guardian",
    "Decision",
    "Approval",
    "Operational",
    "Activation",
    "Execution",
    "Runtime Kernel",
    "Connector",
    "Orchestrator",
    "Mission",
    "Provider",
    "Agent",
    "Skills",
    "Memory",
    "Knowledge",
    "Cognitive",
    "Workflow",
    "Policy",
    "Audit",
    "Artifact",
    "Model Runtime",
    "Execution Runtime",
    "Runtime Service",
)
