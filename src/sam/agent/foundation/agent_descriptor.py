"""Agent Foundation — descriptor agent (immutable DTO).

Sprint 156 — Agent Foundation.
Synchronous, deterministic, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AgentDescriptor:
    """Deskripsi agent (immutable)."""
    agent_id: str
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    runtime_layer: str = "agent"
    implements: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AgentStatus:
    """Status agent (immutable)."""
    agent_id: str
    state: str = "unknown"
    registered: bool = True


@dataclass(frozen=True)
class AgentSummary:
    """Ringkasan agent (immutable)."""
    total_agents: int = 0
    states: dict = field(default_factory=dict)
