"""Agent Contract Framework - WP-11..20 (MISSION-5.3 / IP-5.3-002).

Kontrak interaksi agent: context, request, response, session, interoperability,
explainability, compliance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from .agent_foundation import AgentCapabilityKind


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


# ---- WP-12 Capability Resolution ----

@dataclass(frozen=True)
class AgentCapabilityResolution:
    """Hasil resolusi capability agent."""

    agent_id: str
    capability: AgentCapabilityKind
    resolved: bool

    def as_dict(self) -> dict:
        return {"agent_id": self.agent_id, "capability": self.capability.value, "resolved": self.resolved}


class AgentCapabilityResolver:
    """Resolver capability berdasar kontrak."""

    def __init__(self, contracts: Tuple["AgentInteractionContract", ...] = ()) -> None:
        self._contracts = {c.agent_id: c for c in contracts}

    def register(self, contract: "AgentInteractionContract") -> None:
        self._contracts[contract.agent_id] = contract

    def resolve(self, agent_id: str, capability: AgentCapabilityKind) -> AgentCapabilityResolution:
        contract = self._contracts.get(agent_id)
        resolved = contract is not None and contract.allows(capability)
        return AgentCapabilityResolution(agent_id=agent_id, capability=capability, resolved=resolved)


# ---- WP-11/WP-16 Agent Contract & Session ----

@dataclass(frozen=True)
class AgentInteractionContract:
    """Kontrak interaksi agent dengan SAM."""

    agent_id: str
    contract_id: str
    capabilities: Tuple[AgentCapabilityKind, ...] = field(default_factory=tuple)
    governed: bool = True

    def allows(self, kind: AgentCapabilityKind) -> bool:
        return kind in self.capabilities

    def as_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "contract_id": self.contract_id,
            "capabilities": [k.value for k in self.capabilities],
            "governed": self.governed,
        }


class SessionState(str, Enum):
    """State session interaksi agent."""

    OPEN = "open"
    ACTIVE = "active"
    CLOSED = "closed"


@dataclass(frozen=True)
class AgentSession:
    """Sesi interaksi agent."""

    session_id: str
    agent_id: str
    state: SessionState = SessionState.OPEN
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {"session_id": self.session_id, "agent_id": self.agent_id, "state": self.state.value, "created_at": self.created_at}


# ---- WP-13/14/15 Context, Request, Response ----

@dataclass(frozen=True)
class AgentContext:
    """Context interaksi agent."""

    objective: str
    provenance: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_provenance(self) -> bool:
        return bool(self.provenance)

    def as_dict(self) -> dict:
        return {"objective": self.objective, "provenance": list(self.provenance)}


@dataclass(frozen=True)
class AgentRequest:
    """Request ke agent."""

    request_id: str
    agent_id: str
    capability: AgentCapabilityKind
    context: Optional[AgentContext] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "capability": self.capability.value,
            "context": self.context.as_dict() if self.context else None,
            "parameters": dict(self.parameters),
        }


class AgentResultState(str, Enum):
    """State hasil agent."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class AgentResponse:
    """Response agent."""

    request_id: str
    agent_id: str
    state: AgentResultState = AgentResultState.SUCCESS
    data: Optional[Dict[str, Any]] = None
    error: str = ""

    @property
    def successful(self) -> bool:
        return self.state == AgentResultState.SUCCESS

    def as_dict(self) -> dict:
        return {"request_id": self.request_id, "agent_id": self.agent_id, "state": self.state.value, "data": self.data, "error": self.error}


# ---- WP-17 Interoperability ----

class InteroperabilityState(str, Enum):
    """State interoperability agent."""

    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    PARTIAL = "partial"


@dataclass(frozen=True)
class InteropCheck:
    """Hasil cek interoperability."""

    provider_agent_id: str
    target_agent_id: str
    state: InteroperabilityState = InteroperabilityState.COMPATIBLE

    def as_dict(self) -> dict:
        return {
            "provider_agent_id": self.provider_agent_id,
            "target_agent_id": self.target_agent_id,
            "state": self.state.value,
        }


class InteroperabilityChecker:
    """Memeriksa interoperabilitas antar agent berbasis kontrak."""

    def check(self, provider: AgentInteractionContract, target: AgentInteractionContract) -> InteropCheck:
        shared = set(provider.capabilities) & set(target.capabilities)
        if shared:
            return InteropCheck(provider.agent_id, target.agent_id, InteroperabilityState.COMPATIBLE)
        return InteropCheck(provider.agent_id, target.agent_id, InteroperabilityState.INCOMPATIBLE)


# ---- WP-18 Explainability ----

@dataclass(frozen=True)
class AgentExplanation:
    """Penjelasan interaksi agent."""

    agent_id: str
    request_id: str
    capability: str
    provenance: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"agent_id": self.agent_id, "request_id": self.request_id, "capability": self.capability, "provenance": list(self.provenance)}


# ---- WP-19 Compliance ----

@dataclass(frozen=True)
class AgentContractComplianceResult:
    """Hasil compliance contract agent."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class AgentContractComplianceChecker:
    """Checker compliance contract agent."""

    def check(
        self,
        *,
        contract_followed: bool = True,
        no_authority: bool = True,
        no_execution_bypass: bool = True,
        provenance_preserved: bool = True,
        no_vendor_lockin: bool = True,
    ) -> AgentContractComplianceResult:
        checks = [
            {"code": "CONTRACT_FOLLOWED", "passed": contract_followed},
            {"code": "NO_AUTHORITY", "passed": no_authority},
            {"code": "NO_EXECUTION_BYPASS", "passed": no_execution_bypass},
            {"code": "PROVENANCE_PRESERVED", "passed": provenance_preserved},
            {"code": "NO_VENDOR_LOCKIN", "passed": no_vendor_lockin},
        ]
        return AgentContractComplianceResult(passed=all(c["passed"] for c in checks), checks=tuple(checks))

    def certify(self, **kwargs: Any) -> Dict[str, Any]:
        result = self.check(**kwargs)
        return {"component": "universal_agent.contract_framework", "passed": result.passed, "certified": result.passed, "checks": [c for c in result.checks]}
