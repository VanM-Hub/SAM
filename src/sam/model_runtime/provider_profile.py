"""Provider Profile — profil provider (Sprint 247).

Program B — Model Runtime Integration.
Mapping statis provider. Belum network. Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ProviderProfile:
    """Profil provider (immutable, statis). Tidak inisialisasi koneksi."""
    provider: str
    capabilities: List[str] = field(default_factory=list)
    default_model: str = ""
    requires_key: bool = True
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "capabilities": list(self.capabilities),
            "default_model": self.default_model,
            "requires_key": self.requires_key,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
