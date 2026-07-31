"""ConfigSnapshot (Sprint 262).

Program D - Runtime Services & Deployment.
Snapshot konfigurasi (immutable) untuk audit & determinisme.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class ConfigSnapshot:
    """Snapshot konfigurasi (immutable). Values read-only."""
    values: Mapping[str, Any] = field(default_factory=dict)
    profile: str = "default"
    revision: int = 0

    def __post_init__(self) -> None:
        # MappingProxyType membuat isi dict tidak bisa dimutasi dari luar
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def as_dict(self) -> dict:
        return {
            "values": dict(self.values),
            "profile": self.profile,
            "revision": self.revision,
        }
