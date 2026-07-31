"""Connector Discovery — DTO hasil discovery connector.

Sprint 113 — Connector Discovery.
Discovery murni terhadap registry — tidak ada panggilan eksternal/network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class DiscoveryResult:
    """Hasil discovery seorang connector dari registry."""
    connector_id: str
    name: str
    connector_type: str = "generic"
    source: str = "registry"  # registry | catalog
    found: bool = False
    detail: str = ""


@dataclass(frozen=True)
class DiscoveryReport:
    """Laporan discovery menyeluruh."""
    total_scanned: int = 0
    found: int = 0
    results: List[DiscoveryResult] = field(default_factory=list)
