"""Connector Descriptor — frozen DTOs untuk deskripsi connector.

Sprint 112 — Connector Foundation.
Preview-only, provider-agnostic. Deskripsi murni — tidak ada implementasi provider.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ConnectorDescriptor:
    """Deskripsi dasar sebuah connector (provider-agnostic).

    Tidak mengikat ke provider tertentu (OpenAI/Anthropic/etc.). Hanya mendeskripsikan
    identitas dan jenis generic sebuah connector.
    """
    connector_id: str
    name: str
    connector_type: str = "generic"
    version: str = "1.0.0"
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConnectorStatus:
    """Status operasional connector (preview-only, tidak pernah eksekusi)."""
    connector_id: str
    registered: bool = False
    discovered: bool = False
    bound: bool = False
    state: str = "unknown"  # unknown | defined | registered | discovered | bound


@dataclass(frozen=True)
class ConnectorSummary:
    """Ringkasan statistik connector untuk laporan/bridge."""
    total_connectors: int = 0
    registered: int = 0
    discovered: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
