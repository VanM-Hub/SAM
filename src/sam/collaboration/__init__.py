"""SAM Collaboration — Sprint 26 Fase 1.

Multi-Agent Collaboration: Agent Registry & Discovery.
"""

from .agent import Agent, AGENT_STATUSES
from .registry import AgentRegistry

__all__ = [
    "Agent",
    "AGENT_STATUSES",
    "AgentRegistry",
]
