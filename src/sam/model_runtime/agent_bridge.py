"""Agent Bridge — bridge model <-> agent (read-only) (Sprint 249).

Program B — Model Runtime Integration.
Read-only bridge ke Agent Runtime; tidak menjalankan agent.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AgentBridgeView:
    """View read-only agent (immutable)."""
    agent_id: str = ""
    capabilities: List[str] = field(default_factory=list)
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "capabilities": list(self.capabilities),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class AgentBridge:
    """Bridge model <-> agent. Read-only, tidak mengeksekusi agent."""

    def view(self, agent_id: str, capabilities: List[str] | None = None) -> AgentBridgeView:
        return AgentBridgeView(
            agent_id=agent_id,
            capabilities=list(capabilities or []),
            preview_only=True,
            external_calls=0,
        )
