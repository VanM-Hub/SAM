"""Agent Metadata — metadata agent (immutable DTO).

Sprint 156 — Agent Foundation.
Metadata mendeskripsikan agent secara read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AgentMetadata:
    """Metadata agent (immutable)."""
    agent_id: str
    author: str = ""
    created_at: str = ""
    tags: List[str] = field(default_factory=list)
    readonly: bool = True
