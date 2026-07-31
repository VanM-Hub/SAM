"""Provider Contract — frozen DTO untuk kontrak provider.

Sprint 144 — Provider Foundation (OP-1403).
Kontrak menyatakan jaminan provider terhadap Connector Contract.
Preview-only; tanpa mekanisme eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ProviderContract:
    """Kontrak operasional sebuah provider (preview-only).

    Provider wajib mengimplementasikan kontrak dari Connector Runtime.
    """
    contract_id: str
    provider_id: str
    name: str
    schema_version: str = "1.0"
    guarantees: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProviderContractCompliance:
    """Hasil evaluasi kepatuhan provider terhadap kontrak (deterministik)."""
    contract_id: str
    provider_id: str
    compliant: bool = True
    violations: List[str] = field(default_factory=list)
