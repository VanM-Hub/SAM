"""Agent Capability — kapabilitas agent (immutable DTO).

Sprint 156 — Agent Foundation.
Kapabilitas berisi operasi lifecycle yang didukung agent. Preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AgentOperation:
    """Operasi agent (immutable). Preview-only default."""
    name: str
    preview_only: bool = True


@dataclass(frozen=True)
class AgentCapability:
    """Kapabilitas agent (immutable)."""
    capability_id: str
    agent_id: str
    name: str = ""
    category: str = "lifecycle"
    description: str = ""
    operations: List[AgentOperation] = field(default_factory=list)

    def supports(self, operation: str) -> bool:
        return any(op.name == operation for op in self.operations)
