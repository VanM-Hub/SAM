"""Connector Contract — frozen DTO untuk kontrak connector.

Sprint 112 — Connector Foundation.
Kontrak mendeskripsikan aturan interaksi generic yang dijamin connector.
Tidak ada realisasi provider.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ConnectorContract:
    """Kontrak operasional sebuah connector (preview-only).

    Menyatakan apa yang dijanjikan connector (preview), tanpa mekanisme eksekusi.
    """
    contract_id: str
    connector_id: str
    name: str
    schema_version: str = "1.0"
    guarantees: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ContractCompliance:
    """Hasil evaluasi kepatuhan terhadap kontrak (deterministik, read-only)."""
    contract_id: str
    compliant: bool = True
    violations: List[str] = field(default_factory=list)
