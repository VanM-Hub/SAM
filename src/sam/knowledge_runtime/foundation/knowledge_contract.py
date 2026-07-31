"""Knowledge Contract — kontrak knowledge (immutable DTO, Sprint 180).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class KnowledgeContract:
    """Kontrak knowledge (immutable)."""
    contract_id: str
    knowledge_id: str
    name: str = ""
    guarantees: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class KnowledgeContractCompliance:
    """Hasil cek kepatuhan kontrak (immutable)."""
    contract_id: str
    knowledge_id: str
    compliant: bool = True
    reasons: List[str] = field(default_factory=list)
