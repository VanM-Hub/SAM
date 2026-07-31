"""ConfigProfile (Sprint 262).

Program D - Runtime Services & Deployment.
Named profile untuk kumpulan konfigurasi. Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class ConfigProfile:
    """Profil konfigurasi (immutable)."""
    name: str
    values: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    extends: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required")

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "values": dict(self.values),
            "description": self.description,
            "extends": self.extends,
        }
