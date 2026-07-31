"""Sprint 262 - Runtime Registry: runtime_reference (referensi tanpa meng-import subsystem lain)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .runtime_descriptor import RuntimeDescriptor


@dataclass(frozen=True)
class RuntimeReference:
    """Referensi immutable ke sebuah runtime (metadata-only, read-only)."""

    descriptor: RuntimeDescriptor
    aliases: Tuple[str, ...] = ()
    role: str = "layer"

    def as_dict(self) -> dict:
        return {
            "descriptor": self.descriptor.as_dict(),
            "aliases": list(self.aliases),
            "role": self.role,
        }
