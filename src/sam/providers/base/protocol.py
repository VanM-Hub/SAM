"""Provider Protocol — frozen DTO untuk protokol interaksi provider.

Sprint 144 — Provider Foundation (OP-1403, Protocol).
Mendeskripsikan bentuk interaksi yang dijamin provider terhadap
Connector Runtime. Preview-only, immutable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ProviderProtocol:
    """Protokol interaksi sebuah provider."""
    protocol_id: str
    provider_id: str
    kind: str = "adapter"  # adapter | bridge | contract
    supported_operations: List[str] = field(default_factory=list)
    readonly: bool = True  # selalu read-only / preview di Phase XIV


@dataclass(frozen=True)
class ProtocolCompliance:
    """Hasil evaluasi kepatuhan protokol (deterministik, read-only)."""
    protocol_id: str
    compliant: bool = True
    supported: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
