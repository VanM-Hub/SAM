"""AI Provider Identity - WP-01 (MISSION-5.1 / IP-5.1-001).

Identity model untuk AI Provider. Identity immutable terhadap lifecycle
instance dan tidak digunakan sebagai authority marker.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Tuple


class ProviderType(str, Enum):
    """Klasifikasi jenis AI Provider."""

    CLOUD = "cloud"
    LOCAL = "local"
    ON_PREMISE = "on_premise"
    HYBRID = "hybrid"


class ProviderStatus(str, Enum):
    """Status siklus hidup provider."""

    UNKNOWN = "unknown"
    REGISTERED = "registered"
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RETIRED = "retired"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ProviderIdentity:
    """Identitas AI Provider yang stabil dan immutable.

    Identity tidak pernah menjadi authority marker. Ia hanya mengidentifikasi
    entitas provider, tidak memberikan hak apapun.
    """

    provider_id: str
    name: str
    provider_type: ProviderType = ProviderType.CLOUD
    version: str = "1.0.0"
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    status: ProviderStatus = ProviderStatus.REGISTERED
    created_at: str = field(default_factory=_now_utc)

    @property
    def is_well_formed(self) -> bool:
        return bool(self.provider_id.strip()) and bool(self.name.strip())

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "provider_type": self.provider_type.value,
            "version": self.version,
            "metadata": dict(self.metadata),
            "status": self.status.value,
            "created_at": self.created_at,
            "is_well_formed": self.is_well_formed,
        }
