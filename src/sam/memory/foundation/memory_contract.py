"""Memory Contract — kontrak memori (immutable DTO, Sprint 172).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MemoryContract:
    """Kontrak memori (immutable)."""
    contract_id: str
    memory_id: str
    name: str = ""
    guarantees: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class MemoryContractCompliance:
    """Hasil cek kepatuhan kontrak (immutable)."""
    contract_id: str
    memory_id: str
    compliant: bool = True
    reasons: List[str] = field(default_factory=list)
