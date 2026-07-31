"""Sprint 262 - Runtime Registry: runtime_registry.

Menyimpan seluruh referensi runtime SAM dalam urutan deterministik.
TIDAK hardcode provider; menerima referensi lewat metode register.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .runtime_reference import RuntimeReference


@dataclass(frozen=True)
class RuntimeRegistry:
    """Kumpulan immutable referensi runtime dengan urutan terurut."""

    _refs: Tuple[RuntimeReference, ...] = ()

    def register(self, ref: RuntimeReference) -> "RuntimeRegistry":
        return RuntimeRegistry(_refs=self._refs + (ref,))

    def register_many(self, refs) -> "RuntimeRegistry":
        seq = tuple(refs)
        return RuntimeRegistry(_refs=self._refs + seq)

    @property
    def refs(self) -> Tuple[RuntimeReference, ...]:
        return tuple(sorted(self._refs, key=lambda r: r.descriptor.name.lower()))

    def names(self) -> Tuple[str, ...]:
        return tuple(r.descriptor.name for r in self.refs)

    def __len__(self) -> int:
        return len(self._refs)

    def as_dict(self) -> dict:
        return {
            "runtimes": [r.as_dict() for r in self.refs],
            "count": len(self._refs),
        }
