"""Agent Foundation - WP-02..07 (MISSION-5.3 / IP-5.3-001).

Registry, descriptor, capability, contract, discovery, health untuk Agent
Citizen. Semua read/discovery; tidak ada execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple

from .agent_identity import AgentIdentity, AgentStatus


class AgentCapabilityKind(str, Enum):
    """Jenis capability agent."""

    ANALYZE = "analyze"
    EXECUTE = "execute"
    RESEARCH = "research"
    COORDINATE = "coordinate"
    REPORT = "report"


@dataclass(frozen=True)
class AgentCapability:
    """Satu capability agent."""

    kind: AgentCapabilityKind
    name: str = ""

    def as_dict(self) -> dict:
        return {"kind": self.kind.value, "name": self.name or self.kind.value}


@dataclass(frozen=True)
class AgentDescriptor:
    """Deskripsi agent secara declarative."""

    identity: AgentIdentity
    capabilities: Tuple[AgentCapability, ...] = field(default_factory=tuple)
    interfaces: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def capability(self, kind: AgentCapabilityKind) -> Optional[AgentCapability]:
        for c in self.capabilities:
            if c.kind == kind:
                return c
        return None

    def as_dict(self) -> dict:
        return {
            "identity": self.identity.as_dict(),
            "capabilities": [c.as_dict() for c in self.capabilities],
            "interfaces": list(self.interfaces),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class AgentContract:
    """Kontrak interaksi agent (seragam)."""

    agent_id: str
    contract_id: str
    supports_capability: Tuple[AgentCapabilityKind, ...] = field(default_factory=tuple)
    governed: bool = True

    def allows(self, kind: AgentCapabilityKind) -> bool:
        return kind in self.supports_capability

    def as_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "contract_id": self.contract_id,
            "supports_capability": [k.value for k in self.supports_capability],
            "governed": self.governed,
        }


@dataclass(frozen=True)
class AgentRegistryEntry:
    """Entri registry agent."""

    identity: AgentIdentity
    registered_at: str
    availability: bool = False

    def as_dict(self) -> dict:
        return {"identity": self.identity.as_dict(), "registered_at": self.registered_at, "availability": self.availability}


class AgentRegistry:
    """Registry Agent Citizen (read/discovery)."""

    def __init__(self) -> None:
        self._agents: dict = {}

    def register(self, identity: AgentIdentity, availability: bool = False) -> AgentRegistryEntry:
        entry = AgentRegistryEntry(identity=identity, registered_at=datetime.utcnow().isoformat() + "Z", availability=availability)
        self._agents[identity.agent_id] = entry
        return entry

    def remove(self, agent_id: str) -> bool:
        return self._agents.pop(agent_id, None) is not None

    def lookup(self, agent_id: str) -> Optional[AgentIdentity]:
        entry = self._agents.get(agent_id)
        return entry.identity if entry else None

    def list(self, status: Optional[AgentStatus] = None) -> Tuple[AgentIdentity, ...]:
        items = tuple(e.identity for e in self._agents.values())
        if status is not None:
            items = tuple(i for i in items if i.status == status)
        return items

    def available(self) -> Tuple[AgentIdentity, ...]:
        return tuple(e.identity for e in self._agents.values() if e.availability)

    def size(self) -> int:
        return len(self._agents)

    def validate_registry(self) -> bool:
        return all(e.identity.is_well_formed for e in self._agents.values())


@dataclass(frozen=True)
class AgentDiscoveryResult:
    """Hasil discovery agent."""

    agent_id: str
    capability: Optional[AgentCapabilityKind] = None

    def as_dict(self) -> dict:
        return {"agent_id": self.agent_id, "capability": self.capability.value if self.capability else None}


class AgentDiscovery:
    """Discovery agent berbasis registry & descriptor."""

    def __init__(self, registry: AgentRegistry, descriptors: Tuple[AgentDescriptor, ...] = ()) -> None:
        self._registry = registry
        self._descriptors = {d.identity.agent_id: d for d in descriptors}

    def set_descriptors(self, descriptors: Tuple[AgentDescriptor, ...]) -> None:
        self._descriptors = {d.identity.agent_id: d for d in descriptors}

    def discover_agents(self) -> Tuple[AgentIdentity, ...]:
        return self._registry.list()

    def discover_by_capability(self, kind: AgentCapabilityKind) -> Tuple[AgentDiscoveryResult, ...]:
        return tuple(
            AgentDiscoveryResult(agent_id=aid, capability=kind)
            for aid, desc in self._descriptors.items()
            if desc.capability(kind) is not None
        )

    def descriptors(self) -> Tuple[AgentDescriptor, ...]:
        return tuple(self._descriptors.values())


class AgentHealthState(str, Enum):
    """Kelas status kesehatan agent."""

    UNKNOWN = "unknown"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass(frozen=True)
class AgentHealth:
    """Status kesehatan agent (read-only)."""

    agent_id: str
    state: AgentHealthState = AgentHealthState.UNKNOWN
    latency_ms: Optional[float] = None
    notes: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def healthy(self) -> bool:
        return self.state == AgentHealthState.READY

    def as_dict(self) -> dict:
        return {"agent_id": self.agent_id, "state": self.state.value, "healthy": self.healthy, "latency_ms": self.latency_ms, "notes": list(self.notes)}


class AgentHealthCheck:
    """Assessment kesehatan agent (observasional)."""

    def assess(self, agent_id: str, *, reachable: bool = True, latency_ms: Optional[float] = None, error: Optional[str] = None) -> AgentHealth:
        if error:
            state = AgentHealthState.FAILED
        elif not reachable:
            state = AgentHealthState.DEGRADED
        elif latency_ms is not None and latency_ms > 5000:
            state = AgentHealthState.DEGRADED
        else:
            state = AgentHealthState.READY
        notes = (error,) if error else ()
        return AgentHealth(agent_id=agent_id, state=state, latency_ms=latency_ms, notes=notes)
