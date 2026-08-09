"""AI Provider Registry - WP-02 (MISSION-5.1 / IP-5.1-001).

Registry sebagai sumber discovery AI Provider. Registry TIDAK melakukan
execution; ia hanya menyimpan dan menyajikan informasi provider.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .provider_identity import ProviderIdentity, ProviderStatus


@dataclass(frozen=True)
class RegistryEntry:
    """Entri registry satu provider."""

    identity: ProviderIdentity
    registered_at: str
    availability: bool = False

    def as_dict(self) -> dict:
        return {
            "identity": self.identity.as_dict(),
            "registered_at": self.registered_at,
            "availability": self.availability,
        }


class AIProviderRegistry:
    """Registry AI Provider (read/discovery, bukan execution)."""

    def __init__(self) -> None:
        self._providers: Dict[str, RegistryEntry] = {}

    def register(self, identity: ProviderIdentity, availability: bool = False) -> RegistryEntry:
        from datetime import datetime

        entry = RegistryEntry(
            identity=identity,
            registered_at=datetime.utcnow().isoformat() + "Z",
            availability=availability,
        )
        self._providers[identity.provider_id] = entry
        return entry

    def remove(self, provider_id: str) -> bool:
        return self._providers.pop(provider_id, None) is not None

    def lookup(self, provider_id: str) -> Optional[ProviderIdentity]:
        entry = self._providers.get(provider_id)
        return entry.identity if entry else None

    def set_availability(self, provider_id: str, available: bool) -> bool:
        entry = self._providers.get(provider_id)
        if entry is None:
            return False
        self._providers[provider_id] = RegistryEntry(
            identity=entry.identity,
            registered_at=entry.registered_at,
            availability=available,
        )
        return True

    def list(self, status: Optional[ProviderStatus] = None) -> Tuple[ProviderIdentity, ...]:
        items = tuple(e.identity for e in self._providers.values())
        if status is not None:
            items = tuple(i for i in items if i.status == status)
        return items

    def available(self) -> Tuple[ProviderIdentity, ...]:
        return tuple(
            e.identity for e in self._providers.values() if e.availability
        )

    def metadata_for(self, provider_id: str) -> dict:
        identity = self.lookup(provider_id)
        return identity.as_dict() if identity else {}

    def size(self) -> int:
        return len(self._providers)

    def validate_registry(self) -> bool:
        """Registry valid bila seluruh entri memiliki identity well-formed."""
        return all(e.identity.is_well_formed for e in self._providers.values())
