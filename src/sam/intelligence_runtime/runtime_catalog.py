"""Sprint 262 - Runtime Registry: runtime_catalog (katalog nama runtime struktural)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class RuntimeCatalog:
    """Katalog nama runtime SAM (struktural, bukan provider API)."""

    names: Tuple[str, ...]

    def __len__(self) -> int:
        return len(self.names)

    def has(self, name: str) -> bool:
        return name in self.names

    def as_list(self) -> Tuple[str, ...]:
        return self.names
