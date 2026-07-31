"""Provider Descriptor — frozen DTO untuk deskripsi provider.

Sprint 144 — Provider Foundation (OP-1401).
Deskripsi murni, provider-agnostic. Tidak ada implementasi domain.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ProviderDescriptor:
    """Deskripsi dasar sebuah provider (adapter ke Connector Runtime)."""
    provider_id: str
    name: str
    provider_type: str = "generic"  # filesystem | shell | sqlite | docker | openclaw
    version: str = "1.0.0"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    # id kontrak Connector Runtime yang diimplementasikan provider ini
    implements: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProviderStatus:
    """Status operasional provider (preview-only, tidak pernah eksekusi)."""
    provider_id: str
    registered: bool = False
    discovered: bool = False
    state: str = "unknown"  # unknown | defined | registered | discovered | ready


@dataclass(frozen=True)
class ProviderSummary:
    """Ringkasan statistik provider untuk laporan/bridge."""
    total_providers: int = 0
    registered: int = 0
    discovered: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
