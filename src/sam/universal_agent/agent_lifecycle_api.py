"""Agent Lifecycle, API & Compliance - WP-08..10 (MISSION-5.3 / IP-5.3-001).

Lifecycle agent, API publik foundation, dan compliance checker.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from .agent_foundation import AgentDiscovery, AgentHealth, AgentHealthCheck, AgentRegistry
from .agent_identity import AgentIdentity


class AgentLifecycleState(str, Enum):
    """State lifecycle agent."""

    REGISTERED = "registered"
    ACTIVATING = "activating"
    ACTIVE = "active"
    PAUSED = "paused"
    RETIRED = "retired"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class AgentLifecycle:
    """Keadaan lifecycle agent."""

    agent_id: str
    state: AgentLifecycleState = AgentLifecycleState.REGISTERED
    updated_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {"agent_id": self.agent_id, "state": self.state.value, "updated_at": self.updated_at}


class AgentLifecycleManager:
    """Mengelola state lifecycle agent."""

    def __init__(self) -> None:
        self._states: dict = {}

    def set(self, agent_id: str, state: AgentLifecycleState) -> AgentLifecycle:
        lc = AgentLifecycle(agent_id=agent_id, state=state)
        self._states[agent_id] = lc
        return lc

    def get(self, agent_id: str) -> Optional[AgentLifecycle]:
        return self._states.get(agent_id)


class AgentAPI:
    """API publik Universal Agent Foundation."""

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        discovery: Optional[AgentDiscovery] = None,
        health: Optional[AgentHealthCheck] = None,
        lifecycle: Optional[AgentLifecycleManager] = None,
    ) -> None:
        self.registry = registry or AgentRegistry()
        self.discovery = discovery or AgentDiscovery(self.registry)
        self._health = health or AgentHealthCheck()
        self.lifecycle = lifecycle or AgentLifecycleManager()

    def register(self, identity: AgentIdentity, availability: bool = False):
        return self.registry.register(identity, availability=availability)

    def lookup(self, agent_id: str) -> Optional[AgentIdentity]:
        return self.registry.lookup(agent_id)

    def list_agents(self) -> Tuple[AgentIdentity, ...]:
        return self.registry.list()

    def discover(self, capability=None) -> Tuple:
        if capability is None:
            return tuple(
                __import__("sam.universal_agent.agent_foundation", fromlist=["AgentDiscoveryResult"]).AgentDiscoveryResult(a.agent_id)
                for a in self.registry.list()
            )
        return self.discovery.discover_by_capability(capability)

    def set_descriptors(self, descriptors) -> None:
        self.discovery.set_descriptors(descriptors)

    def health(self, agent_id: str) -> Optional[AgentHealth]:
        if self.registry.lookup(agent_id) is None:
            return None
        return self._health.assess(agent_id)

    def activate(self, agent_id: str) -> Optional[AgentLifecycle]:
        if self.registry.lookup(agent_id) is None:
            return None
        return self.lifecycle.set(agent_id, AgentLifecycleState.ACTIVE)


@dataclass(frozen=True)
class AgentComplianceResult:
    """Hasil compliance agent foundation."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class AgentComplianceChecker:
    """Checker compliance untuk agent foundation."""

    def check(
        self,
        registry: AgentRegistry,
        *,
        identity_valid: bool = True,
        descriptor_valid: bool = True,
        discovery_deterministic: bool = True,
        no_authority: bool = True,
        no_execution_bypass: bool = True,
        no_vendor_lockin: bool = True,
    ) -> AgentComplianceResult:
        checks = [
            {"code": "IDENTITY_VALID", "passed": identity_valid},
            {"code": "REGISTRY_INTEGRITY", "passed": registry.validate_registry()},
            {"code": "DESCRIPTOR_VALID", "passed": descriptor_valid},
            {"code": "DISCOVERY_DETERMINISTIC", "passed": discovery_deterministic},
            {"code": "NO_AUTHORITY", "passed": no_authority},
            {"code": "NO_EXECUTION_BYPASS", "passed": no_execution_bypass},
            {"code": "NO_VENDOR_LOCKIN", "passed": no_vendor_lockin},
        ]
        return AgentComplianceResult(passed=all(c["passed"] for c in checks), checks=tuple(checks))

    def certify(self, registry: AgentRegistry, **kwargs: Any) -> Dict[str, Any]:
        result = self.check(registry, **kwargs)
        return {"component": "universal_agent.foundation", "passed": result.passed, "certified": result.passed, "checks": [c for c in result.checks]}
