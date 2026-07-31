"""Agent Registry — registry agent (read-only query).

Sprint 156 — Agent Foundation.
Mendaftarkan dan menanyakan agent. Tidak memodifikasi subsystem lain.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .agent_descriptor import AgentDescriptor, AgentStatus, AgentSummary
from .agent_capability import AgentCapability
from .agent_contract import AgentContract, AgentContractCompliance
from .agent_metadata import AgentMetadata


@dataclass(frozen=True)
class AgentRegistration:
    """Registrasi agent (immutable)."""
    agent_id: str
    registered: bool = True


class AgentRegistry:
    """Registry agent. Append + read-only query. Deterministik."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, AgentDescriptor] = {}
        self._capabilities: Dict[str, List[AgentCapability]] = {}
        self._contracts: Dict[str, AgentContract] = {}
        self._metadata: Dict[str, AgentMetadata] = {}

    def register(self, descriptor: AgentDescriptor) -> bool:
        if descriptor.agent_id in self._descriptors:
            return False
        self._descriptors[descriptor.agent_id] = descriptor
        return True

    def attach_capability(self, capability: AgentCapability) -> bool:
        self._capabilities.setdefault(capability.agent_id, []).append(capability)
        return True

    def attach_contract(self, contract: AgentContract) -> bool:
        self._contracts[contract.agent_id] = contract
        return True

    def attach_metadata(self, metadata: AgentMetadata) -> bool:
        self._metadata[metadata.agent_id] = metadata
        return True

    def get(self, agent_id: str) -> Optional[AgentDescriptor]:
        return self._descriptors.get(agent_id)

    def get_capabilities(self, agent_id: str) -> List[AgentCapability]:
        return list(self._capabilities.get(agent_id, []))

    def get_contract(self, agent_id: str) -> Optional[AgentContract]:
        return self._contracts.get(agent_id)

    def get_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        return self._metadata.get(agent_id)

    def list_ids(self) -> List[str]:
        return list(self._descriptors.keys())

    def count(self) -> int:
        return len(self._descriptors)

    def summary(self) -> AgentSummary:
        states: Dict[str, int] = {}
        for d in self._descriptors.values():
            states[d.runtime_layer] = states.get(d.runtime_layer, 0) + 1
        return AgentSummary(total_agents=self.count(), states=states)


__all__ = [
    "AgentRegistry", "AgentRegistration",
    "AgentDescriptor", "AgentStatus", "AgentSummary",
    "AgentCapability", "AgentOperation",
    "AgentContract", "AgentContractCompliance",
    "AgentMetadata",
]
