"""ArtifactCatalog — katalog artifact read-only in-memory."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Optional

from ..model.artifact import Artifact


@dataclass(frozen=True)
class ArtifactCatalog:
    """Katalog artifact read-only. Tidak load file, tidak cache."""
    _records: Tuple[Artifact, ...] = ()

    def add(self, artifact: Artifact) -> "ArtifactCatalog":
        return ArtifactCatalog(self._records + (artifact,))

    def get(self, name: str) -> Optional[Artifact]:
        for a in self._records:
            if a.name == name:
                return a
        return None

    def by_kind(self, kind: str) -> Tuple[Artifact, ...]:
        return tuple(a for a in self._records if a.kind == kind)

    def all_records(self) -> Tuple[Artifact, ...]:
        return self._records

    def count(self) -> int:
        return len(self._records)
