"""ArtifactRuntimeRegistry — snapshot runtime terintegrasi (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .artifact_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class ArtifactRuntimeRegistryEntry:
    runtime: str = ""
    integrated: bool = True


@dataclass(frozen=True)
class ArtifactRuntimeRegistry:
    """Snapshot runtime yang terintegrasi. Tidak memutasi runtime lain."""
    _entries: Tuple[ArtifactRuntimeRegistryEntry, ...] = ()

    @classmethod
    def from_route(cls, route: Tuple[str, ...] = INTEGRATION_ROUTE):
        entries = tuple(
            ArtifactRuntimeRegistryEntry(runtime=r, integrated=True)
            for r in route
        )
        return cls(_entries=entries)

    @property
    def entries(self) -> Tuple[ArtifactRuntimeRegistryEntry, ...]:
        return self._entries

    @property
    def count(self) -> int:
        # 14 stages; artifact termasuk di dalamnya
        return len(self._entries)
