"""Agent Contract — kontrak agent (immutable DTO).

Sprint 156 — Agent Foundation.
Kontrak menyatakan jaminan & kendala agent. Preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AgentContract:
    """Kontrak agent (immutable)."""
    contract_id: str
    agent_id: str
    name: str = ""
    guarantees: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AgentContractCompliance:
    """Hasil cek kepatuhan kontrak (immutable)."""
    contract_id: str
    agent_id: str
    compliant: bool = True
    reasons: List[str] = field(default_factory=list)
